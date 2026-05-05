"""
Потоковый парсер k6 JSON-результатов.
Используется модулем analyze.py для генерации графиков.
"""
import json
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu

RESULTS = Path(__file__).resolve().parent / 'results'


def _ts_seconds(ts_str):
    """Быстрое извлечение секунд из ISO timestamp (без datetime)."""
    h = int(ts_str[11:13])
    m = int(ts_str[14:16])
    rest = ts_str[17:].split('+')[0].split('Z')[0]
    s = float(rest)
    return h * 3600 + m * 60 + s


def parse_k6(filepath, need_time=False):
    """
    Потоковый парсинг JSON-файла k6.
    Возвращает dict: values, total, errors, duration_s, [rel_times].
    """
    values = []
    rel_times = []
    total = 0
    errors = 0
    first_sec = None
    last_sec = None

    print(f'  {filepath.name} ...', end=' ', flush=True)

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '"http_req_duration"' not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get('type') != 'Point':
                continue

            data = obj['data']
            val = data['value']
            status = data.get('tags', {}).get('status', '0')

            total += 1
            if not status.startswith('2'):
                errors += 1
            if val < 0:
                continue

            values.append(val)

            ts_str = data['time']
            sec = _ts_seconds(ts_str)
            if first_sec is None:
                first_sec = sec
            last_sec = sec

            if need_time:
                rel_times.append(sec - first_sec)

    dur = (last_sec - first_sec) if (first_sec is not None and last_sec is not None) else 1.0
    if dur <= 0:
        dur = 1.0

    print(f'{len(values)} points, {errors} errors')

    result = {
        'values': np.array(values, dtype=np.float64),
        'total': total,
        'errors': errors,
        'duration_s': dur,
    }
    if need_time:
        result['rel_times'] = np.array(rel_times, dtype=np.float64)
    return result


def find_runs(lang, test, sub=None):
    """Находит все run*.json для заданного теста."""
    if sub:
        d = RESULTS / lang / test / sub
    else:
        d = RESULTS / lang / test
    if not d.exists():
        return []
    return sorted(d.glob('run*.json'))


def pool_data(lang, test, sub=None, need_time=False):
    """
    Загружает и объединяет (pool) все прогоны.
    Возвращает dict: pooled_values, rps_list, err_rate_list, total_reqs, [rel_times].
    """
    runs = find_runs(lang, test, sub)
    if not runs:
        return None

    all_values = []
    all_times = []
    rps_list = []
    err_list = []

    print(f'[{lang}/{test}{"/" + sub if sub else ""}]')
    for fp in runs:
        r = parse_k6(fp, need_time=need_time)
        all_values.append(r['values'])
        rps = r['total'] / r['duration_s']
        rps_list.append(rps)
        err_list.append(r['errors'] / max(r['total'], 1) * 100)
        if need_time and 'rel_times' in r:
            all_times.append(r['rel_times'])

    result = {
        'values': np.concatenate(all_values),
        'rps_list': rps_list,
        'err_list': err_list,
        'rps_mean': np.mean(rps_list),
        'rps_std': np.std(rps_list),
        'err_mean': np.mean(err_list),
    }
    if need_time and all_times:
        result['rel_times'] = all_times[0]
        result['time_values'] = all_values[0]
    return result


def compute_stats(data):
    """Вычисляет статистики из pooled данных."""
    v = data['values']
    return {
        'avg': np.mean(v),
        'med': np.median(v),
        'p95': np.percentile(v, 95),
        'p99': np.percentile(v, 99),
        'max': np.max(v),
        'rps': data['rps_mean'],
        'rps_std': data['rps_std'],
        'err': data['err_mean'],
        'n': len(v),
    }


def mann_whitney(go_vals, py_vals):
    """U-тест Манна-Уитни. Возвращает (U, p-value)."""
    # Подвыборка для скорости, если > 500K точек
    if len(go_vals) > 500_000:
        go_vals = np.random.choice(go_vals, 500_000, replace=False)
    if len(py_vals) > 500_000:
        py_vals = np.random.choice(py_vals, 500_000, replace=False)
    u, p = mannwhitneyu(go_vals, py_vals, alternative='two-sided')
    return u, p


def moving_avg(times, values, window=500):
    """Скользящее среднее для timeline-графиков."""
    idx = np.argsort(times)
    t = times[idx]
    v = values[idx]
    cs = np.cumsum(np.insert(v, 0, 0))
    ma = (cs[window:] - cs[:-window]) / window
    t_ma = t[window // 2: window // 2 + len(ma)]
    return t_ma, ma
