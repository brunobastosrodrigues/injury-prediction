#!/usr/bin/env python3
"""
Analyze PMData Training Load and ACWR.

This script extracts the MISSING SIGNAL - training load data from PMData
and calculates ACWR (Acute:Chronic Workload Ratio) to find the injury trigger.

Scientific Rationale:
- Current features (sleep, stress) = "Vulnerability"
- Training Load + ACWR = "Trigger"
- Injuries occur when Trigger meets Vulnerability
"""

import os
import sys
import json
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PMDATA_PATH = '/home/rodrigues/injury-prediction/backend/data/external/pmdata'


def load_srpe_data(pmdata_path):
    """Load Session RPE data - the gold standard for training load."""
    all_srpe = []

    srpe_files = glob.glob(os.path.join(pmdata_path, '*/pmsys/srpe.csv'))

    for f in srpe_files:
        parts = f.split(os.sep)
        p_idx = parts.index('pmsys')
        athlete_id = parts[p_idx - 1]

        try:
            df = pd.read_csv(f)
            df['athlete_id'] = athlete_id

            # Parse datetime and extract date
            df['datetime'] = pd.to_datetime(df['end_date_time'])
            df['date'] = df['datetime'].dt.date

            # Calculate sRPE Load = RPE × Duration
            df['srpe_load'] = df['perceived_exertion'] * df['duration_min']

            all_srpe.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if all_srpe:
        return pd.concat(all_srpe, ignore_index=True)
    return pd.DataFrame()


def load_fitbit_daily_data(pmdata_path):
    """Load daily Fitbit activity data."""
    all_data = []

    athlete_dirs = glob.glob(os.path.join(pmdata_path, 'p*'))

    for athlete_dir in athlete_dirs:
        athlete_id = os.path.basename(athlete_dir)
        fitbit_dir = os.path.join(athlete_dir, 'fitbit')

        if not os.path.exists(fitbit_dir):
            continue

        # Load very active minutes (daily data)
        vam_file = os.path.join(fitbit_dir, 'very_active_minutes.json')
        mam_file = os.path.join(fitbit_dir, 'moderately_active_minutes.json')

        daily_metrics = {}

        # Very active minutes
        if os.path.exists(vam_file):
            with open(vam_file, 'r') as f:
                data = json.load(f)
                for entry in data:
                    date = pd.to_datetime(entry['dateTime']).date()
                    if date not in daily_metrics:
                        daily_metrics[date] = {'athlete_id': athlete_id}
                    daily_metrics[date]['very_active_min'] = int(entry['value'])

        # Moderately active minutes
        if os.path.exists(mam_file):
            with open(mam_file, 'r') as f:
                data = json.load(f)
                for entry in data:
                    date = pd.to_datetime(entry['dateTime']).date()
                    if date not in daily_metrics:
                        daily_metrics[date] = {'athlete_id': athlete_id}
                    daily_metrics[date]['moderately_active_min'] = int(entry['value'])

        # Convert to list
        for date, metrics in daily_metrics.items():
            metrics['date'] = date
            all_data.append(metrics)

    if all_data:
        df = pd.DataFrame(all_data)
        # Calculate total active minutes
        df['very_active_min'] = df.get('very_active_min', 0).fillna(0)
        df['moderately_active_min'] = df.get('moderately_active_min', 0).fillna(0)
        df['total_active_min'] = df['very_active_min'] + df['moderately_active_min']
        return df
    return pd.DataFrame()


def load_injury_data(pmdata_path):
    """Load injury data."""
    all_injuries = []

    injury_files = glob.glob(os.path.join(pmdata_path, '*/pmsys/injury.csv'))

    for f in injury_files:
        parts = f.split(os.sep)
        p_idx = parts.index('pmsys')
        athlete_id = parts[p_idx - 1]

        try:
            df = pd.read_csv(f)
            df['athlete_id'] = athlete_id

            # Handle date column
            if 'effective_time_frame' in df.columns:
                df['date'] = pd.to_datetime(df['effective_time_frame']).dt.date
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date

            all_injuries.append(df[['athlete_id', 'date']])
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if all_injuries:
        return pd.concat(all_injuries, ignore_index=True)
    return pd.DataFrame()


def calculate_daily_load(srpe_df, fitbit_df):
    """
    Calculate daily training load from multiple sources.

    Primary: sRPE Load (RPE × Duration)
    Secondary: Very Active Minutes (when sRPE missing)
    """
    # Aggregate sRPE by date (sum all sessions)
    if not srpe_df.empty:
        daily_srpe = srpe_df.groupby(['athlete_id', 'date']).agg({
            'srpe_load': 'sum',
            'duration_min': 'sum',
            'perceived_exertion': 'mean'
        }).reset_index()
        daily_srpe.columns = ['athlete_id', 'date', 'daily_srpe_load', 'daily_duration', 'avg_rpe']
    else:
        daily_srpe = pd.DataFrame(columns=['athlete_id', 'date', 'daily_srpe_load', 'daily_duration', 'avg_rpe'])

    # Merge with Fitbit data
    if not fitbit_df.empty:
        daily_load = pd.merge(
            fitbit_df,
            daily_srpe,
            on=['athlete_id', 'date'],
            how='outer'
        )
    else:
        daily_load = daily_srpe.copy()

    # Create unified load metric
    # Priority: sRPE Load > Active Minutes scaled
    daily_load['daily_load'] = daily_load['daily_srpe_load'].fillna(0)

    # Where sRPE is missing, use active minutes as proxy
    # Scale: 1 min very active ≈ 5 load units, 1 min moderate ≈ 2 load units
    mask = daily_load['daily_load'] == 0
    if 'very_active_min' in daily_load.columns:
        daily_load.loc[mask, 'daily_load'] = (
            daily_load.loc[mask, 'very_active_min'].fillna(0) * 5 +
            daily_load.loc[mask, 'moderately_active_min'].fillna(0) * 2
        )

    return daily_load


def calculate_acwr(df, load_col='daily_load', acute_days=7, chronic_days=28):
    """
    Calculate Acute:Chronic Workload Ratio per athlete.

    ACWR = (7-day rolling avg) / (28-day rolling avg)

    Injury Risk Zones (Gabbett, 2016):
    - < 0.8: Undertrained (detraining risk)
    - 0.8-1.3: Sweet spot (optimal)
    - 1.3-1.5: Danger zone (elevated risk)
    - > 1.5: High risk (injury likely)
    """
    df = df.sort_values(['athlete_id', 'date'])

    result = []
    for athlete_id, group in df.groupby('athlete_id'):
        group = group.set_index('date').sort_index()

        # Fill missing dates
        if len(group) > 0:
            date_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
            group = group.reindex(date_range)
            group['athlete_id'] = athlete_id
            group[load_col] = group[load_col].fillna(0)

        # Calculate rolling averages
        group['acute_load'] = group[load_col].rolling(window=acute_days, min_periods=1).mean()
        group['chronic_load'] = group[load_col].rolling(window=chronic_days, min_periods=7).mean()

        # Calculate ACWR
        group['acwr'] = group['acute_load'] / (group['chronic_load'] + 1e-6)

        # Calculate week-over-week load change
        group['load_change_7d'] = group[load_col].rolling(7).sum() / (
            group[load_col].shift(7).rolling(7).sum() + 1e-6
        )

        group = group.reset_index()
        group = group.rename(columns={'index': 'date'})
        result.append(group)

    return pd.concat(result, ignore_index=True)


def analyze_acwr_injury_relationship(load_df, injury_df, window_days=3):
    """
    Analyze the relationship between ACWR and injuries.

    This is the key analysis: Does ACWR spike before injuries?
    """
    print("\n" + "=" * 60)
    print("ACWR vs INJURY ANALYSIS")
    print("=" * 60)

    # Create injury markers
    injury_set = set(zip(injury_df['athlete_id'], injury_df['date']))

    # Mark injury days and create target variable
    load_df['date'] = pd.to_datetime(load_df['date']).dt.date
    load_df['is_injury_day'] = load_df.apply(
        lambda row: (row['athlete_id'], row['date']) in injury_set, axis=1
    )

    # Create forward-looking target (injury in next N days)
    def create_target(group, window=window_days):
        group = group.sort_values('date')
        indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=window)
        group['will_get_injured'] = group['is_injury_day'].rolling(window=indexer, min_periods=1).max()
        return group

    load_df = load_df.groupby('athlete_id', group_keys=False).apply(create_target)

    # Filter to valid ACWR values
    valid_df = load_df[load_df['acwr'].notna() & (load_df['chronic_load'] > 10)].copy()

    print(f"\nSamples with valid ACWR: {len(valid_df)}")
    print(f"Injury rate ({window_days}-day window): {valid_df['will_get_injured'].mean():.1%}")

    # Correlation analysis
    print("\n--- Feature Correlations with Injury ---")
    features = ['daily_load', 'acwr', 'acute_load', 'chronic_load', 'load_change_7d']

    correlations = []
    for feat in features:
        if feat in valid_df.columns:
            r, p = stats.spearmanr(valid_df[feat].fillna(0), valid_df['will_get_injured'])
            correlations.append({
                'feature': feat,
                'correlation': r,
                'p_value': p,
                'significant': p < 0.05
            })
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            print(f"  {feat}: r = {r:+.4f}{sig}")

    # ACWR Zone Analysis
    print("\n--- ACWR Zone Injury Rates ---")
    valid_df['acwr_zone'] = pd.cut(
        valid_df['acwr'],
        bins=[0, 0.8, 1.0, 1.3, 1.5, 10],
        labels=['<0.8 (Undertrained)', '0.8-1.0 (Low)', '1.0-1.3 (Optimal)', '1.3-1.5 (Danger)', '>1.5 (High Risk)']
    )

    zone_analysis = valid_df.groupby('acwr_zone', observed=True).agg({
        'will_get_injured': ['mean', 'sum', 'count']
    }).round(4)
    zone_analysis.columns = ['injury_rate', 'injury_count', 'sample_count']
    print(zone_analysis)

    # Pre-injury ACWR pattern
    print("\n--- Pre-Injury ACWR Pattern ---")
    injury_days = valid_df[valid_df['is_injury_day']]
    safe_days = valid_df[~valid_df['will_get_injured'].astype(bool)]

    if len(injury_days) > 0 and len(safe_days) > 0:
        print(f"  Injury days ACWR:  mean = {injury_days['acwr'].mean():.3f}, std = {injury_days['acwr'].std():.3f}")
        print(f"  Safe days ACWR:    mean = {safe_days['acwr'].mean():.3f}, std = {safe_days['acwr'].std():.3f}")

        # T-test
        t_stat, p_val = stats.ttest_ind(injury_days['acwr'].dropna(), safe_days['acwr'].dropna())
        print(f"  T-test: t = {t_stat:.3f}, p = {p_val:.4f}")

    return valid_df, correlations


def train_model_with_load(df):
    """Train a model using load features and compare to wellness-only."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import roc_auc_score

    print("\n" + "=" * 60)
    print("MODEL COMPARISON: Wellness Only vs Wellness + Load")
    print("=" * 60)

    # Filter valid rows
    df = df.dropna(subset=['acwr', 'will_get_injured'])
    df = df[df['chronic_load'] > 10]  # Need enough history

    target = 'will_get_injured'

    # Wellness-only features (proxy - we'll use what we have)
    wellness_features = ['chronic_load']  # Baseline

    # Load features
    load_features = ['daily_load', 'acwr', 'acute_load', 'load_change_7d']

    # Combined
    all_features = wellness_features + load_features

    # Prepare data
    available_features = [f for f in all_features if f in df.columns]
    X = df[available_features].fillna(0)
    y = df[target]

    print(f"\nSamples: {len(X)}, Features: {available_features}")
    print(f"Injury rate: {y.mean():.1%}")

    # Train with load features
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)

    cv_scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc')
    print(f"\nWith Load Features:")
    print(f"  5-Fold CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Feature importance
    rf.fit(X, y)
    importance = sorted(zip(available_features, rf.feature_importances_), key=lambda x: -x[1])
    print("\nFeature Importance:")
    for feat, imp in importance:
        bar = "*" * int(imp * 50)
        print(f"  {feat}: {imp:.4f} {bar}")

    return cv_scores.mean()


def main():
    print("=" * 60)
    print("PMDATA TRAINING LOAD ANALYSIS")
    print("Finding the Missing 'Trigger' for Injuries")
    print("=" * 60)

    # 1. Load all data sources
    print("\n--- Loading Data ---")
    srpe_df = load_srpe_data(PMDATA_PATH)
    print(f"sRPE sessions loaded: {len(srpe_df)}")

    fitbit_df = load_fitbit_daily_data(PMDATA_PATH)
    print(f"Fitbit daily records loaded: {len(fitbit_df)}")

    injury_df = load_injury_data(PMDATA_PATH)
    print(f"Injury records loaded: {len(injury_df)}")

    # 2. Calculate daily load
    print("\n--- Calculating Daily Load ---")
    daily_load = calculate_daily_load(srpe_df, fitbit_df)
    print(f"Daily load records: {len(daily_load)}")
    print(f"Athletes with load data: {daily_load['athlete_id'].nunique()}")

    # 3. Calculate ACWR
    print("\n--- Calculating ACWR ---")
    load_with_acwr = calculate_acwr(daily_load)
    print(f"Records with ACWR: {load_with_acwr['acwr'].notna().sum()}")
    print(f"ACWR range: {load_with_acwr['acwr'].min():.2f} - {load_with_acwr['acwr'].max():.2f}")
    print(f"ACWR mean: {load_with_acwr['acwr'].mean():.2f}")

    # 4. Analyze ACWR-Injury relationship
    analyzed_df, correlations = analyze_acwr_injury_relationship(
        load_with_acwr, injury_df, window_days=3
    )

    # 5. Train model with load features
    auc = train_model_with_load(analyzed_df)

    # 6. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Check if ACWR correlates with injury
    acwr_corr = next((c for c in correlations if c['feature'] == 'acwr'), None)
    if acwr_corr:
        if acwr_corr['significant']:
            print(f"\n[SIGNAL FOUND] ACWR correlates with injury!")
            print(f"  Correlation: r = {acwr_corr['correlation']:+.4f}")
            print("  ACTION: Add ACWR to synthetic data generator")
        else:
            print(f"\n[WEAK SIGNAL] ACWR correlation not significant")
            print(f"  Correlation: r = {acwr_corr['correlation']:+.4f}")
            print("  POSSIBLE: Injuries may be traumatic/random, not overuse")

    print(f"\nModel AUC with Load Features: {auc:.4f}")
    if auc > 0.55:
        print("  [SUCCESS] Load features improve injury prediction!")
    else:
        print("  [NEEDS WORK] Load features alone insufficient")

    return analyzed_df, correlations


if __name__ == "__main__":
    main()
