# scripts/analyze_pmdata_patterns.py
"""
Reverse-engineer the "Injury Formula" from PMData.

This script analyzes real-world injury patterns to understand:
1. Which features correlate with injury?
2. What's the "injury signature" (Safe Days vs Pre-Injury Days)?
3. What are the feature importances from a model trained on real data?

The goal is to calibrate synthetic_data_generation/injury_simulation.py
to match real-world patterns.
"""

import sys
import os
import pandas as pd
import numpy as np
from scipy import stats

# Add project paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.pm_adapter import PMDataAdapter


def load_pmdata():
    """Load and prepare PMData for analysis."""
    print("=" * 60)
    print("LOADING PMDATA")
    print("=" * 60)

    adapter = PMDataAdapter('backend/data/external/pmdata')
    df = adapter.load_and_unify()

    print(f"Loaded {len(df)} samples")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nInjury rate: {df['will_get_injured'].mean():.2%}")
    print(f"  - Safe days: {(df['will_get_injured'] == 0).sum()}")
    print(f"  - Pre-injury days: {(df['will_get_injured'] == 1).sum()}")

    return df


def correlation_scan(df):
    """
    Calculate Pearson and Spearman correlations between features and injury.

    Returns ranked list of features by absolute correlation.
    """
    print("\n" + "=" * 60)
    print("STEP 1: CORRELATION SCAN")
    print("=" * 60)

    target = 'will_get_injured'
    feature_cols = [c for c in df.columns if c not in ['date', 'athlete_id', 'is_injured', 'will_get_injured']]

    results = []

    for feat in feature_cols:
        if feat in df.columns:
            # Pearson correlation
            pearson_r, pearson_p = stats.pearsonr(df[feat], df[target])

            # Spearman correlation (better for non-linear relationships)
            spearman_r, spearman_p = stats.spearmanr(df[feat], df[target])

            results.append({
                'feature': feat,
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_r': spearman_r,
                'spearman_p': spearman_p,
                'abs_pearson': abs(pearson_r),
                'abs_spearman': abs(spearman_r)
            })

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('abs_spearman', ascending=False)

    print("\nFeature Correlations with Injury (sorted by |Spearman|):")
    print("-" * 60)
    print(f"{'Feature':<20} {'Pearson':>10} {'Spearman':>10} {'Direction':<12}")
    print("-" * 60)

    for _, row in results_df.iterrows():
        direction = "+" if row['spearman_r'] > 0 else "-"
        sig = "***" if row['spearman_p'] < 0.001 else "**" if row['spearman_p'] < 0.01 else "*" if row['spearman_p'] < 0.05 else ""
        print(f"{row['feature']:<20} {row['pearson_r']:>+.4f} {row['spearman_r']:>+.4f}{sig}  {direction} injury risk")

    print("\n*** p<0.001, ** p<0.01, * p<0.05")

    # Top 3 features
    print("\n" + "=" * 60)
    print("TOP 3 INJURY PREDICTORS (by Spearman correlation):")
    print("=" * 60)
    for i, (_, row) in enumerate(results_df.head(3).iterrows(), 1):
        direction = "increases" if row['spearman_r'] > 0 else "decreases"
        print(f"  {i}. {row['feature']}: r={row['spearman_r']:+.4f} (higher values {direction} injury risk)")

    return results_df


def injury_signature(df):
    """
    Compare feature means on Safe Days vs Pre-Injury Days.

    This reveals the "injury signature" - what changes before an injury?
    """
    print("\n" + "=" * 60)
    print("STEP 2: INJURY SIGNATURE (Safe Days vs Pre-Injury Days)")
    print("=" * 60)

    target = 'will_get_injured'
    feature_cols = [c for c in df.columns if c not in ['date', 'athlete_id', 'is_injured', 'will_get_injured']]

    safe_days = df[df[target] == 0]
    preinjury_days = df[df[target] == 1]

    print(f"\nSafe days: n={len(safe_days)}")
    print(f"Pre-injury days: n={len(preinjury_days)}")

    results = []

    for feat in feature_cols:
        if feat in df.columns:
            safe_mean = safe_days[feat].mean()
            preinjury_mean = preinjury_days[feat].mean()
            delta = preinjury_mean - safe_mean
            delta_pct = (delta / (safe_mean + 1e-8)) * 100

            # T-test for significance
            t_stat, p_value = stats.ttest_ind(safe_days[feat], preinjury_days[feat])

            results.append({
                'feature': feat,
                'safe_mean': safe_mean,
                'preinjury_mean': preinjury_mean,
                'delta': delta,
                'delta_pct': delta_pct,
                't_stat': t_stat,
                'p_value': p_value
            })

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('delta_pct', key=abs, ascending=False)

    print("\nFeature Changes Before Injury:")
    print("-" * 70)
    print(f"{'Feature':<20} {'Safe Mean':>10} {'Pre-Inj Mean':>12} {'Delta':>10} {'Delta %':>10}")
    print("-" * 70)

    for _, row in results_df.iterrows():
        sig = "***" if row['p_value'] < 0.001 else "**" if row['p_value'] < 0.01 else "*" if row['p_value'] < 0.05 else ""
        print(f"{row['feature']:<20} {row['safe_mean']:>10.4f} {row['preinjury_mean']:>12.4f} {row['delta']:>+10.4f} {row['delta_pct']:>+9.1f}%{sig}")

    print("\n*** p<0.001, ** p<0.01, * p<0.05")

    # Key insights
    print("\n" + "=" * 60)
    print("KEY INJURY SIGNATURE INSIGHTS:")
    print("=" * 60)

    for _, row in results_df.head(5).iterrows():
        if abs(row['delta_pct']) > 1:
            direction = "INCREASES" if row['delta'] > 0 else "DECREASES"
            print(f"  - {row['feature']} {direction} by {abs(row['delta_pct']):.1f}% before injury")

    return results_df


def feature_importance_rf(df):
    """
    Train a Random Forest on PMData and extract feature importances.

    This tells us which features the model finds most predictive.
    """
    print("\n" + "=" * 60)
    print("STEP 3: RANDOM FOREST FEATURE IMPORTANCE")
    print("=" * 60)

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score

    target = 'will_get_injured'
    feature_cols = [c for c in df.columns if c not in ['date', 'athlete_id', 'is_injured', 'will_get_injured']]

    X = df[feature_cols]
    y = df[target]

    print(f"\nTraining Random Forest on {len(X)} samples, {len(feature_cols)} features...")

    # Train model
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        min_samples_split=10,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )

    # Cross-validation score
    cv_scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc')
    print(f"5-Fold CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Fit on full data for feature importance
    rf.fit(X, y)

    # Extract importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nFeature Importance Ranking:")
    print("-" * 40)
    print(f"{'Rank':<6} {'Feature':<20} {'Importance':>12}")
    print("-" * 40)

    for i, (_, row) in enumerate(importance_df.iterrows(), 1):
        bar = "*" * int(row['importance'] * 50)
        print(f"{i:<6} {row['feature']:<20} {row['importance']:>12.4f}  {bar}")

    # Top 3 features
    print("\n" + "=" * 60)
    print("TOP 3 FEATURES BY RANDOM FOREST IMPORTANCE:")
    print("=" * 60)
    for i, (_, row) in enumerate(importance_df.head(3).iterrows(), 1):
        print(f"  {i}. {row['feature']}: importance={row['importance']:.4f}")

    return importance_df, rf


def generate_calibration_recommendations(corr_df, signature_df, importance_df):
    """
    Generate actionable recommendations for calibrating injury_simulation.py.
    """
    print("\n" + "=" * 60)
    print("CALIBRATION RECOMMENDATIONS FOR injury_simulation.py")
    print("=" * 60)

    # Find the top predictors
    top_by_corr = corr_df.head(3)['feature'].tolist()
    top_by_importance = importance_df.head(3)['feature'].tolist()

    # Find consensus features
    consensus = set(top_by_corr) & set(top_by_importance)

    print("\n1. CONSENSUS TOP PREDICTORS (appear in both correlation and RF):")
    for feat in consensus:
        corr_row = corr_df[corr_df['feature'] == feat].iloc[0]
        imp_row = importance_df[importance_df['feature'] == feat].iloc[0]
        sig_row = signature_df[signature_df['feature'] == feat].iloc[0]

        direction = "increases" if corr_row['spearman_r'] > 0 else "decreases"
        print(f"   - {feat}: corr={corr_row['spearman_r']:+.4f}, importance={imp_row['importance']:.4f}")
        print(f"     Pre-injury delta: {sig_row['delta_pct']:+.1f}%")
        print(f"     Interpretation: Higher {feat} {direction} injury risk")

    print("\n2. ACTION ITEMS FOR injury_simulation.py:")

    # Check if soreness is a top predictor
    if 'soreness_score' in top_by_importance[:3]:
        print("   [HIGH PRIORITY] Add 'soreness' as a primary injury risk factor")
        print("   - Current simulation may underweight muscle soreness")

    if 'fatigue_score' in top_by_importance[:3]:
        print("   [HIGH PRIORITY] Increase weight of 'fatigue' in injury probability")
        print("   - Real injuries correlate strongly with fatigue accumulation")

    if 'recovery_score' in top_by_importance[:3]:
        print("   [MEDIUM PRIORITY] Recovery/readiness is a key protective factor")
        print("   - Higher recovery should reduce injury probability")

    if 'stress_score' in top_by_importance[:3]:
        print("   [MEDIUM PRIORITY] Stress contributes to injury risk")
    else:
        print("   [NOTE] Stress may be less important than currently weighted")

    if 'sleep_quality_daily' in top_by_importance[:3]:
        print("   [MEDIUM PRIORITY] Sleep quality affects injury risk")
    else:
        print("   [NOTE] Sleep quality may be less important than currently weighted")

    print("\n3. SPECIFIC WEIGHT ADJUSTMENTS:")

    # Calculate suggested weights based on importance
    total_imp = importance_df['importance'].sum()
    for _, row in importance_df.iterrows():
        weight = (row['importance'] / total_imp) * 100
        print(f"   {row['feature']}: suggest ~{weight:.0f}% weight in injury formula")


def main():
    """Run the full PMData analysis pipeline."""
    print("=" * 60)
    print("PMDATA INJURY PATTERN ANALYSIS")
    print("Reverse-engineering the real-world injury formula")
    print("=" * 60)

    # Load data
    df = load_pmdata()

    # Run analyses
    corr_df = correlation_scan(df)
    signature_df = injury_signature(df)
    importance_df, rf_model = feature_importance_rf(df)

    # Generate recommendations
    generate_calibration_recommendations(corr_df, signature_df, importance_df)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: REAL-WORLD INJURY FORMULA FROM PMDATA")
    print("=" * 60)

    top_features = importance_df.head(3)['feature'].tolist()
    print(f"\nTop 3 predictive features: {top_features}")
    print("\nNext step: Modify injury_simulation.py to weight these features accordingly.")

    return {
        'correlations': corr_df,
        'signature': signature_df,
        'importance': importance_df,
        'model': rf_model
    }


if __name__ == "__main__":
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        results = main()
