"""
Анализ результатов нагрузочного тестирования Go vs Python.
Генерация 10 профессиональных графиков (300 DPI).

Запуск:
    pip install matplotlib scipy numpy
    python benchmarks/analyze.py

Результаты: benchmarks/results/charts/
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# Добавление пути для импорта парсера
sys.path.insert(0, str(Path(__file__).parent))
from analyze_parser import (
    RESULTS, pool_data, compute_stats, mann_whitney, moving_avg, find_runs
)

CHARTS = RESULTS / 'charts'
C_GO, C_PY = '#2E86AB', '#A23B72'

T1_SCENARIOS = ['s_browsing', 's_orders', 's_admin', 's_analytics']
T1_LABELS = ['Просмотр\nкаталога', 'Оформление\nзаказов', 'Администри-\nрование', 'Аналитика']
T4_CPUS = ['1cpu', '2cpu', '4cpu']
T4_NUMS = [1, 2, 4]

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 12,
    'axes.titlesize': 14, 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11,
    'legend.fontsize': 11, 'figure.dpi': 150,
    'savefig.dpi': 300, 'savefig.bbox': 'tight',
    'axes.grid': True, 'grid.alpha': 0.3,
})


def fmt(v):
    if v < 1: return f'{v:.2f}'
    if v < 100: return f'{v:.1f}'
    return f'{v:.0f}'


def save(fig, name):
    p = CHARTS / name
    fig.savefig(p)
    plt.close(fig)
    print(f'  ✓ {name}')


# ═══════════════════════════════════════════
# ГРАФИК 1: T1 — RPS по 4 сценариям
# ═══════════════════════════════════════════
def chart_t1_rps(t1_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(T1_SCENARIOS))
    w = 0.35

    go_rps = [t1_data[('go', s)]['rps_mean'] for s in T1_SCENARIOS]
    py_rps = [t1_data[('python', s)]['rps_mean'] for s in T1_SCENARIOS]
    go_err = [t1_data[('go', s)]['rps_std'] for s in T1_SCENARIOS]
    py_err = [t1_data[('python', s)]['rps_std'] for s in T1_SCENARIOS]

    b1 = ax.bar(x - w/2, go_rps, w, label='Go', color=C_GO, alpha=0.85, yerr=go_err, capsize=4)
    b2 = ax.bar(x + w/2, py_rps, w, label='Python', color=C_PY, alpha=0.85, yerr=py_err, capsize=4)

    for bars, color in [(b1, C_GO), (b2, C_PY)]:
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                    fmt(b.get_height()), ha='center', va='bottom',
                    fontsize=9, color=color, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(T1_LABELS)
    ax.set_ylabel('Запросов в секунду (RPS)')
    ax.set_title('T1: Пропускная способность по бизнес-сценариям')
    ax.legend()
    save(fig, 't1_rps_comparison.png')


# ═══════════════════════════════════════════
# ГРАФИК 2: T1 — p95 задержка по 4 сценариям
# ═══════════════════════════════════════════
def chart_t1_p95(t1_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(T1_SCENARIOS))
    w = 0.35

    go_p95 = [np.percentile(t1_data[('go', s)]['values'], 95) for s in T1_SCENARIOS]
    py_p95 = [np.percentile(t1_data[('python', s)]['values'], 95) for s in T1_SCENARIOS]

    use_log = max(py_p95) / max(max(go_p95), 0.01) > 10

    b1 = ax.bar(x - w/2, go_p95, w, label='Go', color=C_GO, alpha=0.85)
    b2 = ax.bar(x + w/2, py_p95, w, label='Python', color=C_PY, alpha=0.85)

    if use_log:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    for bars, color in [(b1, C_GO), (b2, C_PY)]:
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                    f'{fmt(b.get_height())} мс', ha='center', va='bottom',
                    fontsize=9, color=color, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(T1_LABELS)
    ax.set_ylabel('Задержка p95 (мс)')
    ax.set_title('T1: Задержка 95-го перцентиля по бизнес-сценариям')
    ax.legend()
    save(fig, 't1_p95_comparison.png')


# ═══════════════════════════════════════════
# ГРАФИК 3: T1 — CDF (сетка 2x2)
# ═══════════════════════════════════════════
def chart_t1_cdf(t1_data):
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    titles = ['Просмотр каталога', 'Оформление заказов',
              'Администрирование', 'Аналитика']

    for idx, sc in enumerate(T1_SCENARIOS):
        ax = axes[idx // 2][idx % 2]
        for lang, color in [('go', C_GO), ('python', C_PY)]:
            v = t1_data[(lang, sc)]['values']
            # Подвыборка для быстрой отрисовки
            if len(v) > 10000:
                v = np.random.choice(v, 10000, replace=False)
            sv = np.sort(v)
            cdf = np.arange(1, len(sv)+1) / len(sv) * 100
            ax.plot(sv, cdf, color=color, linewidth=1.5, label=lang.capitalize())

        for pct, ls in [(50, '--'), (95, '-.'), (99, ':')]:
            ax.axhline(y=pct, color='gray', linestyle=ls, alpha=0.5, linewidth=0.8)

        ax.set_xlabel('Задержка (мс)')
        ax.set_ylabel('Процентиль (%)')
        ax.set_title(titles[idx])
        ax.legend(loc='lower right')
        ax.set_ylim(0, 101)

    fig.suptitle('T1: Кумулятивное распределение задержки (CDF)', fontsize=15, y=1.01)
    fig.tight_layout()
    save(fig, 't1_cdf_grid.png')


# ═══════════════════════════════════════════
# ГРАФИК 4: T2 — Стресс-тест (timeline)
# ═══════════════════════════════════════════
def chart_t2_timeline(go_data, py_data):
    fig, ax = plt.subplots(figsize=(13, 5))

    # Стадии T2: 0-2m(500), 2-4m(1000), 4-6m(1500), 6-8m(2000), 8-9m(0)
    stages = [(0,120,'500 VU'), (120,240,'1000 VU'),
              (240,360,'1500 VU'), (360,480,'2000 VU'), (480,540,'Cool-down')]
    colors_bg = ['#e8f4f8', '#d1e9f0', '#b8dde8', '#9fd1e0', '#f0f0f0']
    for (s, e, lbl), c in zip(stages, colors_bg):
        ax.axvspan(s, e, alpha=0.3, color=c)
        ax.text((s+e)/2, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 100,
                lbl, ha='center', va='bottom', fontsize=8, color='#555')

    for data, color, label in [(go_data, C_GO, 'Go'), (py_data, C_PY, 'Python')]:
        if data and 'rel_times' in data:
            t, ma = moving_avg(data['rel_times'], data['time_values'], window=300)
            ax.plot(t, ma, color=color, linewidth=1.5, label=label, alpha=0.9)

    ax.set_xlabel('Время теста (секунды)')
    ax.set_ylabel('Задержка (мс), скользящее среднее')
    ax.set_title('T2: Стресс-тест — деградация под нагрузкой до 2000 VU')
    ax.legend(loc='upper left')
    save(fig, 't2_stress_timeline.png')


# ═══════════════════════════════════════════
# ГРАФИК 5: T3 — Spike-тест (timeline)
# ═══════════════════════════════════════════
def chart_t3_timeline(go_data, py_data):
    fig, ax = plt.subplots(figsize=(13, 5))

    # Стадии T3: spike zones
    ax.axvspan(60, 100, alpha=0.15, color='red', label='Скачок (1000 VU)')
    ax.axvspan(220, 260, alpha=0.15, color='red')

    for data, color, label in [(go_data, C_GO, 'Go'), (py_data, C_PY, 'Python')]:
        if data and 'rel_times' in data:
            win = min(200, len(data['time_values']) // 20)
            win = max(win, 10)
            t, ma = moving_avg(data['rel_times'], data['time_values'], window=win)
            ax.plot(t, ma, color=color, linewidth=1.5, label=label, alpha=0.9)

    ax.set_xlabel('Время теста (секунды)')
    ax.set_ylabel('Задержка (мс), скользящее среднее')
    ax.set_title('T3: Тест на скачки нагрузки — реакция и восстановление')
    ax.legend(loc='upper left')
    save(fig, 't3_spike_timeline.png')


# ═══════════════════════════════════════════
# ГРАФИКИ 6-7: T4 — Масштабируемость
# ═══════════════════════════════════════════
def chart_t4(t4_data):
    # График 6: RPS vs CPU
    fig, ax = plt.subplots(figsize=(8, 5))
    for lang, color, marker in [('go', C_GO, 'o'), ('python', C_PY, 's')]:
        rps = []
        for cpu in T4_CPUS:
            d = t4_data.get((lang, cpu))
            rps.append(d['rps_mean'] if d else 0)
        ax.plot(T4_NUMS, rps, color=color, marker=marker, markersize=8,
                linewidth=2, label=lang.capitalize())
        for i, v in enumerate(rps):
            ax.text(T4_NUMS[i], v, f'  {fmt(v)}', va='bottom', fontsize=9, color=color)

    # Идеальная линейная масштабируемость (пунктир)
    go_1cpu = t4_data.get(('go', '1cpu'))
    if go_1cpu:
        ideal = [go_1cpu['rps_mean'] * n for n in T4_NUMS]
        ax.plot(T4_NUMS, ideal, '--', color='gray', alpha=0.5, label='Идеальное масштабирование')

    ax.set_xlabel('Количество CPU')
    ax.set_ylabel('Запросов в секунду (RPS)')
    ax.set_title('T4: Вертикальная масштабируемость — пропускная способность')
    ax.set_xticks(T4_NUMS)
    ax.legend()
    save(fig, 't4_scalability_rps.png')

    # График 7: p95 vs CPU
    fig, ax = plt.subplots(figsize=(8, 5))
    for lang, color, marker in [('go', C_GO, 'o'), ('python', C_PY, 's')]:
        p95 = []
        for cpu in T4_CPUS:
            d = t4_data.get((lang, cpu))
            p95.append(np.percentile(d['values'], 95) if d else 0)
        ax.plot(T4_NUMS, p95, color=color, marker=marker, markersize=8,
                linewidth=2, label=lang.capitalize())
        for i, v in enumerate(p95):
            ax.text(T4_NUMS[i], v, f'  {fmt(v)} мс', va='bottom', fontsize=9, color=color)

    ax.set_xlabel('Количество CPU')
    ax.set_ylabel('Задержка p95 (мс)')
    ax.set_title('T4: Вертикальная масштабируемость — задержка')
    ax.set_xticks(T4_NUMS)
    ax.legend()
    save(fig, 't4_scalability_p95.png')


# ═══════════════════════════════════════════
# ГРАФИК 8: T5 — Смешанная нагрузка
# ═══════════════════════════════════════════
def chart_t5(go_data, py_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    metrics = ['RPS', 'Avg', 'p50', 'p95', 'p99']

    go_s = compute_stats(go_data)
    py_s = compute_stats(py_data)

    go_vals = [go_s['rps'], go_s['avg'], go_s['med'], go_s['p95'], go_s['p99']]
    py_vals = [py_s['rps'], py_s['avg'], py_s['med'], py_s['p95'], py_s['p99']]

    x = np.arange(len(metrics))
    w = 0.35
    b1 = ax.bar(x - w/2, go_vals, w, label='Go', color=C_GO, alpha=0.85)
    b2 = ax.bar(x + w/2, py_vals, w, label='Python', color=C_PY, alpha=0.85)

    use_log = max(py_vals) / max(max(go_vals), 0.01) > 10
    if use_log:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    for bars, color in [(b1, C_GO), (b2, C_PY)]:
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                    fmt(b.get_height()), ha='center', va='bottom',
                    fontsize=9, color=color, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylabel('Значение (RPS / мс)')
    ax.set_title('T5: Смешанная production-нагрузка — сравнение метрик')
    ax.legend()
    save(fig, 't5_mixed_comparison.png')


# ═══════════════════════════════════════════
# ГРАФИК 9: Сводная таблица
# ═══════════════════════════════════════════
def chart_summary(all_stats, mw_results):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis('off')

    headers = ['Тест / Сценарий', 'Go RPS', 'Go p95 (мс)', 'Py RPS', 'Py p95 (мс)',
               'Разница RPS', 'Разница p95', 'p-value']
    rows = []
    for key, (go_s, py_s) in sorted(all_stats.items()):
        rps_ratio = f'{go_s["rps"]/max(py_s["rps"],0.01):.1f}×'
        p95_ratio = f'{py_s["p95"]/max(go_s["p95"],0.001):.1f}×'
        pv = mw_results.get(key, (0, 1.0))[1]
        pv_str = f'{pv:.2e}' if pv > 0.001 else '< 0.001'
        rows.append([
            key, fmt(go_s['rps']), fmt(go_s['p95']),
            fmt(py_s['rps']), fmt(py_s['p95']),
            rps_ratio, p95_ratio, pv_str
        ])

    table = ax.table(cellText=rows, colLabels=headers, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    for j in range(len(headers)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')
    for i in range(1, len(rows) + 1):
        for j in range(len(headers)):
            cell = table[i, j]
            cell.set_facecolor('#f0f4f8' if i % 2 == 0 else '#ffffff')

    ax.set_title('Сводная таблица результатов (все тесты)', fontsize=14, pad=20)
    save(fig, 'summary_table.png')


# ═══════════════════════════════════════════
# ГРАФИК 10: Сравнение ошибок T2/T3
# ═══════════════════════════════════════════
def chart_errors(err_data):
    fig, ax = plt.subplots(figsize=(8, 5))
    tests = list(err_data.keys())
    x = np.arange(len(tests))
    w = 0.35

    go_err = [err_data[t]['go'] for t in tests]
    py_err = [err_data[t]['python'] for t in tests]

    b1 = ax.bar(x - w/2, go_err, w, label='Go', color=C_GO, alpha=0.85)
    b2 = ax.bar(x + w/2, py_err, w, label='Python', color=C_PY, alpha=0.85)

    for bars, color in [(b1, C_GO), (b2, C_PY)]:
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                    f'{b.get_height():.2f}%', ha='center', va='bottom',
                    fontsize=9, color=color, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(tests)
    ax.set_ylabel('Процент ошибок (%)')
    ax.set_title('Устойчивость к нагрузке — процент отказов')
    ax.legend()
    save(fig, 'summary_error_rates.png')


# ═══════════════════════════════════════════
# CSV со всеми метриками
# ═══════════════════════════════════════════
def save_csv(all_stats, mw_results):
    path = CHARTS / 'summary_stats.csv'
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Test', 'Lang', 'RPS', 'Avg_ms', 'Median_ms', 'p95_ms',
                     'p99_ms', 'Max_ms', 'Error_%', 'N_requests', 'MW_p_value'])
        for key, (go_s, py_s) in sorted(all_stats.items()):
            pv = mw_results.get(key, (0, 1.0))[1]
            for lang, s in [('Go', go_s), ('Python', py_s)]:
                w.writerow([key, lang, f'{s["rps"]:.2f}', f'{s["avg"]:.2f}',
                            f'{s["med"]:.2f}', f'{s["p95"]:.2f}', f'{s["p99"]:.2f}',
                            f'{s["max"]:.2f}', f'{s["err"]:.2f}', s['n'], f'{pv:.2e}'])
    print(f'  ✓ summary_stats.csv')


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    os.makedirs(CHARTS, exist_ok=True)
    all_stats = {}
    mw_results = {}
    err_data = {}

    # ── T1: Load Test ──
    print('\n══ T1: Load Test ══')
    t1_data = {}
    for sc in T1_SCENARIOS:
        for lang in ['go', 'python']:
            d = pool_data(lang, 't1_load', sc)
            if d:
                t1_data[(lang, sc)] = d

    if len(t1_data) == 8:  # 4 сценария × 2 языка
        chart_t1_rps(t1_data)
        chart_t1_p95(t1_data)
        chart_t1_cdf(t1_data)

        for sc in T1_SCENARIOS:
            key = f'T1/{sc}'
            go_s = compute_stats(t1_data[('go', sc)])
            py_s = compute_stats(t1_data[('python', sc)])
            all_stats[key] = (go_s, py_s)
            _, p = mann_whitney(t1_data[('go', sc)]['values'],
                                t1_data[('python', sc)]['values'])
            mw_results[key] = (0, p)
    else:
        print('Неполные данные T1, пропускаем графики')

    # ── T2: Stress Test ──
    print('\n══ T2: Stress Test ══')
    t2_go = pool_data('go', 't2_stress', need_time=True)
    t2_py = pool_data('python', 't2_stress', need_time=True)

    if t2_go and t2_py:
        chart_t2_timeline(t2_go, t2_py)
        go_s = compute_stats(t2_go)
        py_s = compute_stats(t2_py)
        all_stats['T2/stress'] = (go_s, py_s)
        err_data['T2 Стресс'] = {'go': go_s['err'], 'python': py_s['err']}

    # ── T3: Spike Test ──
    print('\n══ T3: Spike Test ══')
    t3_go = pool_data('go', 't3_spike', need_time=True)
    t3_py = pool_data('python', 't3_spike', need_time=True)

    if t3_go and t3_py:
        chart_t3_timeline(t3_go, t3_py)
        go_s = compute_stats(t3_go)
        py_s = compute_stats(t3_py)
        all_stats['T3/spike'] = (go_s, py_s)
        err_data['T3 Скачок'] = {'go': go_s['err'], 'python': py_s['err']}

    # ── T4: Scalability Test ──
    print('\n══ T4: Scalability Test ══')
    t4_data = {}
    for cpu in T4_CPUS:
        for lang in ['go', 'python']:
            d = pool_data(lang, 't4_scale', cpu)
            if d:
                t4_data[(lang, cpu)] = d

    if len(t4_data) >= 4:
        chart_t4(t4_data)
        for cpu in T4_CPUS:
            key = f'T4/{cpu}'
            go_d = t4_data.get(('go', cpu))
            py_d = t4_data.get(('python', cpu))
            if go_d and py_d:
                all_stats[key] = (compute_stats(go_d), compute_stats(py_d))

    # ── T5: Mixed Test ──
    print('\n══ T5: Mixed Test ══')
    t5_go = pool_data('go', 't5_mixed')
    t5_py = pool_data('python', 't5_mixed')

    if t5_go and t5_py:
        chart_t5(t5_go, t5_py)
        go_s = compute_stats(t5_go)
        py_s = compute_stats(t5_py)
        all_stats['T5/mixed'] = (go_s, py_s)
        err_data['T5 Смешанная'] = {'go': go_s['err'], 'python': py_s['err']}
        _, p = mann_whitney(t5_go['values'], t5_py['values'])
        mw_results['T5/mixed'] = (0, p)

    # ── Сводные графики ──
    print('\n══ Сводные графики ══')
    if all_stats:
        chart_summary(all_stats, mw_results)
        save_csv(all_stats, mw_results)
    if err_data:
        chart_errors(err_data)

    print(f'\n Готово! Все графики в: {CHARTS}/')


if __name__ == '__main__':
    main()
