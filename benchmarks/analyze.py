import json, os, argparse
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Единые настройки matplotlib (DPI=300 для печати)
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 12,
    'axes.titlesize': 14, 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11,
    'legend.fontsize': 11, 'figure.dpi': 150,
    'savefig.dpi': 300, 'savefig.bbox': 'tight',
    'axes.grid': True, 'grid.alpha': 0.3,
})

# Контрастные цвета, различимые при ч/б печати
COLOR_GO = '#2E86AB'   # синий — Go
COLOR_PY = '#A23B72'   # пурпурный — Python

# Названия сценариев с типом HTTP-метода
SCENARIO_TITLES = {
    's1_browsing': 'S1: Просмотр каталога (GET)',
    's2_orders': 'S2: Оформление заказов (POST/GET)',
    's3_admin': 'S3: Администрирование (PATCH)',
    's4_analytics': 'S4: Аналитические запросы (GET)',
    's5_mixed': 'S5: Смешанная нагрузка',
}


def parse_k6_json(file_path):
    """Парсинг JSON k6. Возвращает (DataFrame, error_rate%)."""
    print(f"Reading {file_path}...")
    data = []
    total_lines = 0
    error_lines = 0
    with open(file_path, 'r') as f:
        for line in f:
            line_data = json.loads(line)
            if line_data.get('type') == 'Point' and line_data.get('metric') == 'http_req_duration':
                point = line_data['data']
                tags = point.get('tags', {})
                value = point['value']
                status = tags.get('status', 'unknown')
                total_lines += 1
                # Статус не 2xx = ошибка
                if not status.startswith('2'):
                    error_lines += 1
                # Отрицательные значения — артефакт Docker/WSL2
                if value < 0:
                    continue
                data.append({
                    'timestamp': point['time'],
                    'value': value,
                    'method': tags.get('method', 'unknown'),
                    'name': tags.get('name', 'unknown'),
                    'status': status
                })
    if not data:
        return None, 0.0

    df = pl.DataFrame(data)
    df = df.with_columns(
        timestamp=pl.col('timestamp').str.to_datetime("%Y-%m-%dT%H:%M:%S%.f%Z")
    )
    error_rate = (error_lines / total_lines * 100) if total_lines > 0 else 0.0
    return df, error_rate


def get_title(name):
    """Название сценария для заголовка графика."""
    return SCENARIO_TITLES.get(name, name.replace('_', ' ').title())


def fmt_val(v):
    """Форматирование: <1->2 знака, <100->1 знак, >=100->целое."""
    if v < 1:
        return f"{v:.2f}"
    if v < 100:
        return f"{v:.1f}"
    return f"{v:.0f}"


def moving_avg(times, values, win):
    """Скользящее среднее через кумулятивные суммы O(n)."""
    idx = np.argsort(times)
    t_s = times[idx]; v_s = values[idx]
    cs = np.cumsum(np.insert(v_s, 0, 0))
    ma = (cs[win:] - cs[:-win]) / win
    t_ma = t_s[win // 2: win // 2 + len(ma)]
    return t_ma, ma


def generate_report(go_df, py_df, go_err, py_err, scenario_name, output_dir):
    """Генерация 5 PNG-графиков + CSV со статистикой для одного сценария."""
    os.makedirs(output_dir, exist_ok=True)
    title = get_title(scenario_name)

    # Расчёт статистик: RPS, avg, median, p95, p99, max -> CSV
    stats = []
    for name, df, err in [('Go', go_df, go_err), ('Python', py_df, py_err)]:
        if df is not None:
            dur = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            rps = len(df) / dur if dur > 0 else 0
            stats.append({
                'Language': name, 'RPS': round(rps, 2),
                'Avg (ms)': round(df['value'].mean(), 2),
                'Median (ms)': round(df['value'].median(), 2),
                'p95 (ms)': round(df['value'].quantile(0.95), 2),
                'p99 (ms)': round(df['value'].quantile(0.99), 2),
                'Max (ms)': round(df['value'].max(), 2),
                'Error Rate (%)': round(err, 2),
                'Total Requests': len(df),
            })
    stats_df = pl.DataFrame(stats)
    print(f"\n--- {title} ---")
    print(stats_df)
    stats_df.write_csv(os.path.join(output_dir, f"stats_{scenario_name}.csv"))

    if go_df is None or py_df is None:
        return

    go_v = go_df['value'].to_numpy()
    py_v = py_df['value'].to_numpy()

    # ГРАФИК 1: Задержка во времени
    # Время нормализовано к t=0 (тесты запускались последовательно).
    # Скользящее среднее + полоса p5-p95 для разброса.
    fig, ax = plt.subplots(figsize=(12, 5))
    go_ts = go_df['timestamp'].to_numpy()
    py_ts = py_df['timestamp'].to_numpy()
    go_rel = (go_ts - go_ts.min()).astype('timedelta64[ms]').astype(float) / 1000.0
    py_rel = (py_ts - py_ts.min()).astype('timedelta64[ms]').astype(float) / 1000.0
    win = max(10, len(go_v) // 100)

    go_t_ma, go_ma = moving_avg(go_rel, go_v, win)
    py_t_ma, py_ma = moving_avg(py_rel, py_v, win)
    ax.plot(go_t_ma, go_ma, color=COLOR_GO, linewidth=1.5, label='Go', alpha=0.9)
    ax.plot(py_t_ma, py_ma, color=COLOR_PY, linewidth=1.5, label='Python', alpha=0.9)

    # Полоса p5-p95 по 50 бинам
    for rel_t, vals, color in [(go_rel, go_v, COLOR_GO), (py_rel, py_v, COLOR_PY)]:
        edges = np.linspace(rel_t.min(), rel_t.max(), 51)
        centers = (edges[:-1] + edges[1:]) / 2
        p5, p95 = [], []
        for i in range(50):
            m = (rel_t >= edges[i]) & (rel_t < edges[i+1])
            bv = vals[m]
            if len(bv) > 0:
                p5.append(np.percentile(bv, 5)); p95.append(np.percentile(bv, 95))
            else:
                p5.append(np.nan); p95.append(np.nan)
        ax.fill_between(centers, p5, p95, color=color, alpha=0.12)

    ax.set_xlabel('Время теста (секунды)')
    ax.set_ylabel('Задержка (мс)')
    ax.set_title(f'{title} — Задержка во времени')
    ax.legend(loc='upper right')
    fig.savefig(os.path.join(output_dir, f"latency_time_{scenario_name}.png"))
    plt.close(fig)

    # ГРАФИК 2: Boxplot (раздельные шкалы Go/Python, без выбросов)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [1, 1]})
    for ax_i, (vals, color, label) in enumerate([(go_v, COLOR_GO, 'Go'), (py_v, COLOR_PY, 'Python')]):
        ax = axes[ax_i]
        bp = ax.boxplot([vals], patch_artist=True, showfliers=False, widths=0.5,
                        medianprops=dict(color='black', linewidth=2),
                        whiskerprops=dict(linewidth=1.2), capprops=dict(linewidth=1.2))
        bp['boxes'][0].set_facecolor(color); bp['boxes'][0].set_alpha(0.7)
        med = np.median(vals); p95 = np.percentile(vals, 95); p99 = np.percentile(vals, 99)
        ax.set_title(label, fontsize=14, fontweight='bold')
        ax.set_ylabel('Задержка (мс)' if ax_i == 0 else '')
        ax.set_xticks([])
        txt = f"Med: {fmt_val(med)} мс\np95: {fmt_val(p95)} мс\np99: {fmt_val(p99)} мс"
        ax.text(0.95, 0.95, txt, transform=ax.transAxes, fontsize=10,
                va='top', ha='right', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    fig.suptitle(f'{title} — Распределение задержки', fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, f"latency_dist_{scenario_name}.png"))
    plt.close(fig)

    # ГРАФИК 3: Столбцы метрик (авто-лог. шкала при разнице >20x)
    fig, ax = plt.subplots(figsize=(10, 5))
    metrics = ['Avg', 'Median', 'p95', 'p99', 'Max']
    go_bars = [np.mean(go_v), np.median(go_v), np.percentile(go_v, 95),
               np.percentile(go_v, 99), np.max(go_v)]
    py_bars = [np.mean(py_v), np.median(py_v), np.percentile(py_v, 95),
               np.percentile(py_v, 99), np.max(py_v)]
    x = np.arange(len(metrics)); w = 0.35
    use_log = max(py_bars) / max(max(go_bars), 0.01) > 20

    b_go = ax.bar(x - w/2, go_bars, w, label='Go', color=COLOR_GO, alpha=0.85)
    b_py = ax.bar(x + w/2, py_bars, w, label='Python', color=COLOR_PY, alpha=0.85)
    if use_log:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    for bar, color in [(b_go, COLOR_GO), (b_py, COLOR_PY)]:
        for b in bar:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h, fmt_val(h),
                    ha='center', va='bottom', fontsize=9, color=color, fontweight='bold')

    ax.set_xticks(x); ax.set_xticklabels(metrics)
    ax.set_ylabel('Задержка (мс)')
    ax.set_title(f'{title} — Сравнение метрик')
    ax.legend()
    fig.savefig(os.path.join(output_dir, f"metrics_bar_{scenario_name}.png"))
    plt.close(fig)

    # ГРАФИК 4: CDF (чем левее кривая — тем быстрее сервис)
    fig, ax = plt.subplots(figsize=(10, 5))
    for vals, color, label in [(go_v, COLOR_GO, 'Go'), (py_v, COLOR_PY, 'Python')]:
        sv = np.sort(vals)
        cdf = np.arange(1, len(sv)+1) / len(sv) * 100
        ax.plot(sv, cdf, color=color, linewidth=2, label=label)
    for pct, style in [(50, '--'), (95, '-.'), (99, ':')]:
        ax.axhline(y=pct, color='gray', linestyle=style, alpha=0.5, linewidth=0.8)
        ax.text(ax.get_xlim()[0], pct + 0.5, f'p{pct}', fontsize=9, color='gray')
    ax.set_xlabel('Задержка (мс)'); ax.set_ylabel('Процентиль (%)')
    ax.set_title(f'{title} — Кумулятивное распределение (CDF)')
    ax.legend(loc='lower right'); ax.set_ylim(0, 101)
    fig.savefig(os.path.join(output_dir, f"cdf_{scenario_name}.png"))
    plt.close(fig)

    # ГРАФИК 5: Сводная таблица с колонкой «Разница» (py/go)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')

    row_labels = ['RPS', 'Avg', 'Медиана (p50)', 'p95', 'p99', 'Max', 'Error rate', 'Всего запросов']
    go_rps = stats[0]['RPS'] if len(stats) > 0 else 0
    py_rps = stats[1]['RPS'] if len(stats) > 1 else 0

    go_col = [
        f"{go_rps:.1f}",
        f"{fmt_val(np.mean(go_v))} мс", f"{fmt_val(np.median(go_v))} мс",
        f"{fmt_val(np.percentile(go_v, 95))} мс", f"{fmt_val(np.percentile(go_v, 99))} мс",
        f"{fmt_val(np.max(go_v))} мс", f"{go_err:.2f}%", f"{len(go_v)}",
    ]
    py_col = [
        f"{py_rps:.1f}",
        f"{fmt_val(np.mean(py_v))} мс", f"{fmt_val(np.median(py_v))} мс",
        f"{fmt_val(np.percentile(py_v, 95))} мс", f"{fmt_val(np.percentile(py_v, 99))} мс",
        f"{fmt_val(np.max(py_v))} мс", f"{py_err:.2f}%", f"{len(py_v)}",
    ]

    def ratio(go_val, py_val):
        """Во сколько раз Python медленнее Go (или наоборот)."""
        if go_val == 0 and py_val == 0:
            return "—"
        if go_val == 0:
            return "∞"
        r = py_val / go_val
        if r >= 1:
            return f"{r:.1f}×"
        return f"{1/r:.1f}× (Go)"

    ratio_vals = [
        ratio(py_rps, go_rps),  # RPS инвертирован: больше = лучше
        ratio(np.mean(go_v), np.mean(py_v)),
        ratio(np.median(go_v), np.median(py_v)),
        ratio(np.percentile(go_v, 95), np.percentile(py_v, 95)),
        ratio(np.percentile(go_v, 99), np.percentile(py_v, 99)),
        ratio(np.max(go_v), np.max(py_v)),
        ratio(go_err, py_err) if go_err > 0 else ("—" if py_err == 0 else f"∞"),
        "—",
    ]

    cell_text = []
    for i in range(len(row_labels)):
        cell_text.append([row_labels[i], go_col[i], py_col[i], ratio_vals[i]])

    table = ax.table(
        cellText=cell_text,
        colLabels=['Метрика', 'Go', 'Python', 'Разница'],
        loc='center', cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)

    # Стилизация таблицы
    for j in range(4):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')
    for i in range(1, len(row_labels) + 1):
        for j in range(4):
            cell = table[i, j]
            cell.set_facecolor('#f0f4f8' if i % 2 == 0 else '#ffffff')
            if j == 1:
                cell.set_text_props(color=COLOR_GO, fontweight='bold')
            elif j == 2:
                cell.set_text_props(color=COLOR_PY, fontweight='bold')

    ax.set_title(f'{title} — Сводная таблица', fontsize=14, pad=20)
    fig.savefig(os.path.join(output_dir, f"table_{scenario_name}.png"))
    plt.close(fig)

    print(f"  → 5 графиков сохранены в {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Анализ результатов нагрузочного тестирования Go vs Python"
    )
    parser.add_argument("--go", required=True, help="Путь к JSON-файлу результатов Go")
    parser.add_argument("--py", required=True, help="Путь к JSON-файлу результатов Python")
    parser.add_argument("--name", required=True, help="Имя сценария (s1_browsing, s2_orders, ...)")
    args = parser.parse_args()

    go_data, go_err = parse_k6_json(args.go)
    py_data, py_err = parse_k6_json(args.py)

    generate_report(go_data, py_data, go_err, py_err, args.name, "benchmarks/results/charts")
