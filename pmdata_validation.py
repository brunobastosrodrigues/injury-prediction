import csv
import glob
import math
import os
import json

def calculate_correlation(x, y):
    if len(x) != len(y) or len(x) == 0:
        return 0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x_sq = sum(xi**2 for xi in x)
    sum_y_sq = sum(yi**2 for yi in y)
    sum_xy = sum(xi*yi for xi, yi in zip(x, y))
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x_sq - sum_x**2) * (n * sum_y_sq - sum_y**2))
    
    if denominator == 0:
        return 0
    return numerator / denominator

def validate_pmdata():
    print("--- PMData Validation (Standard Lib) ---")
    
    # 1. PMData Analysis
    pmdata_path = 'data/pmdata'
    wellness_files = glob.glob(f'{pmdata_path}/*/pmsys/wellness.csv')
    
    pm_sleep_quality = []
    pm_readiness = []
    
    for f in wellness_files:
        with open(f, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    sq = float(row['sleep_quality'])
                    readiness = float(row['readiness'])
                    pm_sleep_quality.append(sq)
                    pm_readiness.append(readiness)
                except (ValueError, KeyError):
                    continue
    
    if not pm_sleep_quality:
        print("No PMData found.")
        return

    print(f"PMData samples: {len(pm_sleep_quality)}")
    pm_corr = calculate_correlation(pm_sleep_quality, pm_readiness)
    print(f"PMData Correlation (Sleep Quality vs Readiness): {pm_corr:.4f}")

    # 2. Synthetic Data Analysis
    # Using the CSV dataset since we don't have parquet tools
    csv_dataset = 'data/raw/dataset_20251224_150028_919185'
    print(f"Using synthetic dataset: {csv_dataset}")
    
    synth_sleep_quality = []
    synth_body_battery = []
    
    daily_csv = os.path.join(csv_dataset, 'daily_data.csv')
    if os.path.exists(daily_csv):
        with open(daily_csv, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    sq = float(row['sleep_quality'])
                    bb = float(row['body_battery_morning'])
                    synth_sleep_quality.append(sq)
                    synth_body_battery.append(bb)
                except (ValueError, KeyError):
                    continue
    
    if not synth_sleep_quality:
        print("No synthetic data found.")
        return

    print(f"Synthetic samples: {len(synth_sleep_quality)}")
    synth_corr = calculate_correlation(synth_sleep_quality, synth_body_battery)
    print(f"Synthetic Correlation (Sleep Quality vs Body Battery Morning): {synth_corr:.4f}")

    print("\n--- Summary ---")
    diff = abs(pm_corr - synth_corr)
    print(f"Correlation Difference: {diff:.4f}")
    if diff < 0.1:
        print("VALIDATION SUCCESS: Synthetic correlations closely match real-world data!")
    elif diff < 0.2:
        print("VALIDATION SEMI-SUCCESS: Correlations are in the same ballpark.")
    else:
        print("VALIDATION WARNING: Significant difference in correlations detected.")

if __name__ == "__main__":
    validate_pmdata()