import json
import os
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse

# Регламентация визуального оформления графиков
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
sns.set_style("whitegrid")

def parse_k6_json(file_path):
    """
    Выполнение высокопроизводительного парсинга JSON-файла результатов k6.
    Применение библиотеки Polars для обеспечения оптимального времени обработки 
    больших массивов первичных данных.
    """
    print(f"Reading {file_path}...")
    
    # Итерационный разбор постройного JSON-вывода k6. 
    # Фильтрация данных по типу 'Point' и метрике 'http_req_duration'.
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            line_data = json.loads(line)
            if line_data.get('type') == 'Point' and line_data.get('metric') == 'http_req_duration':
                point = line_data['data']
                tags = point.get('tags', {})
                value = point['value']
                # Filter out negative values: WSL2/Docker Desktop clock sync artifact on Windows.
                # Negative durations are physically impossible and skew statistics (min metric).
                if value < 0:
                    continue
                data.append({
                    'timestamp': point['time'],
                    'value': value,
                    'method': tags.get('method', 'unknown'),
                    'name': tags.get('name', 'unknown'),
                    'status': tags.get('status', 'unknown')
                })

                
    if not data:
        return None
        
    df = pl.DataFrame(data)
    # Приведение временных меток к формату datetime для обеспечения возможности анализа временных рядов
    df = df.with_columns(
        timestamp = pl.col('timestamp').str.to_datetime("%Y-%m-%dT%H:%M:%S%.f%Z")
    )
    return df

def generate_report(go_df, py_df, scenario_name, output_dir):
    """Генерация графических материалов и статистических отчетов."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Расчет дескриптивных статистических показателей
    stats = []
    for name, df in [('Go', go_df), ('Python', py_df)]:
        if df is not None:
            stats.append({
                'Language': name,
                'RPS': len(df) / (df['timestamp'].max() - df['timestamp'].min()).total_seconds(),
                'Avg Latency (ms)': df['value'].mean(),
                'p95 Latency (ms)': df['value'].quantile(0.95),
                'p99 Latency (ms)': df['value'].quantile(0.99),
                'Max Latency (ms)': df['value'].max(),
                'Total Requests': len(df)
            })
    
    stats_df = pl.DataFrame(stats)
    print("\n--- Summary Statistics ---")
    print(stats_df)
    stats_df.write_csv(os.path.join(output_dir, f"stats_{scenario_name}.csv"))

    # Построение компаративных визуализаций
    if go_df is not None and py_df is not None:
        # Интеграция данных различных реализаций для сопоставления
        go_plt = go_df.with_columns(lang=pl.lit('Go'))
        py_plt = py_df.with_columns(lang=pl.lit('Python'))
        all_data = pl.concat([go_plt, py_plt]).to_pandas()

        # Визуализация распределения показателей задержки (Boxenplot)
        plt.figure(figsize=(10, 6))
        sns.boxenplot(data=all_data, x='lang', y='value', palette=['#2E86AB', '#A23B72'])
        plt.title(f"Latency Distribution: {scenario_name.replace('_', ' ').title()}")
        plt.ylabel("Latency (ms)")
        plt.xlabel("Language")
        plt.savefig(os.path.join(output_dir, f"latency_dist_{scenario_name}.png"), dpi=300)
        plt.close()

        # Построение временных рядов задержки (Moving Average Analysis)
        plt.figure(figsize=(12, 6))
        all_data['time_sec'] = (all_data['timestamp'] - all_data['timestamp'].min()).dt.total_seconds()
        sns.lineplot(data=all_data, x='time_sec', y='value', hue='lang', alpha=0.5)
        plt.title(f"Latency Over Time: {scenario_name.replace('_', ' ').title()}")
        plt.ylabel("Latency (ms)")
        plt.xlabel("Time (seconds)")
        plt.savefig(os.path.join(output_dir, f"latency_time_{scenario_name}.png"), dpi=300)
        plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", required=True, help="Path to Go results JSON")
    parser.add_argument("--py", required=True, help="Path to Python results JSON")
    parser.add_argument("--name", required=True, help="Scenario name")
    args = parser.parse_args()

    go_data = parse_k6_json(args.go)
    py_data = parse_k6_json(args.py)
    
    generate_report(go_data, py_data, args.name, "benchmarks/results/charts")
