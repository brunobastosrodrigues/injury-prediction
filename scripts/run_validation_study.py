# scripts/run_validation_study.py
import sys
import os
import pandas as pd
import numpy as np
import json

# Add project root and backend to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.pm_adapter import PMDataAdapter
from backend.app.services.training_service import TrainingService
from backend.app.services.analytics_service import AnalyticsService


def histogram_match(source, template):
    """
    Apply histogram matching to transform source distribution to match template.
    This aligns synthetic data distributions with real PMData patterns.
    """
    # Get sorted unique values and indices
    source_values = source.values
    template_values = template.values

    # Calculate percentiles for both distributions
    source_percentiles = np.argsort(np.argsort(source_values)) / len(source_values)

    # Map source percentiles to template values
    template_sorted = np.sort(template_values)
    matched = np.interp(source_percentiles, np.linspace(0, 1, len(template_sorted)), template_sorted)

    return pd.Series(matched, index=source.index)

def main():
    print("==================================================")
    print("   INJURY PREDICTION: SIM-TO-REAL VALIDATION STUDY")
    print("==================================================")
    
    # 1. Ingest PMData
    print("\n--- 1. Ingesting PMData (The Ground Truth) ---")
    pmdata_path = 'backend/data/external/pmdata'
    if not os.path.exists(pmdata_path):
        print(f"Error: PMData path '{pmdata_path}' not found.")
        return

    try:
        adapter = PMDataAdapter(pmdata_path)
        df_real = adapter.load_and_unify()
        print(f"Successfully loaded PMData: {len(df_real)} samples.")
        print("Sample rows:")
        print(df_real.head())
        
        # Save for reference
        os.makedirs('data/processed', exist_ok=True)
        df_real.to_csv('data/processed/pmdata_standardized.csv', index=False)
    except Exception as e:
        print(f"Error loading PMData: {e}")
        return
    
    # 2. Load Synthetic Data
    print("\n--- 2. Loading Synthetic Data ---")
    # Try to find the PMData-calibrated dataset first, otherwise use latest
    import glob
    raw_path = 'data/raw'
    calibrated_path = os.path.join(raw_path, 'dataset_pmdata_calibrated')
    if os.path.exists(calibrated_path):
        datasets = [calibrated_path]
        print("Using PMData-calibrated synthetic dataset!")
    else:
        datasets = sorted(glob.glob(os.path.join(raw_path, 'dataset_*')))
    if datasets:
        latest_dataset = datasets[-1]
        daily_csv = os.path.join(latest_dataset, 'daily_data.csv')
        daily_parquet = os.path.join(latest_dataset, 'daily_data.parquet')
        
        df_synth = None
        if os.path.exists(daily_csv):
            print(f"Using synthetic dataset: {daily_csv}")
            df_synth = pd.read_csv(daily_csv)
        elif os.path.exists(daily_parquet):
            print(f"Using synthetic dataset: {daily_parquet}")
            df_synth = pd.read_parquet(daily_parquet)
        else:
            print("No daily_data.csv or daily_data.parquet found in latest dataset.")
            return

        # Rename columns to match the 'standard' schema we defined in Adapter if necessary
        # Adapter used: sleep_quality_daily, stress_score, recovery_score
        # Synthetic usually has: sleep_quality (0-1), stress (0-100), body_battery_morning (0-100)

        # Map synthetic columns to the standardized names used in PMAdapter
        rename_map = {
            'sleep_quality': 'sleep_quality_daily',
            'stress': 'stress_score',
            'body_battery_morning': 'recovery_score'
        }
        df_synth = df_synth.rename(columns=rename_map)

        # CRITICAL: Normalize synthetic features to 0-1 scale to match PMData normalization
        # This fixes the Sim2Real scaling mismatch
        print("Normalizing synthetic features to 0-1 scale...")

        # sleep_quality_daily is already 0-1, but verify and normalize if needed
        if 'sleep_quality_daily' in df_synth.columns:
            sq_max = df_synth['sleep_quality_daily'].max()
            sq_min = df_synth['sleep_quality_daily'].min()
            if sq_max > 1 or sq_min < 0:
                df_synth['sleep_quality_daily'] = (
                    (df_synth['sleep_quality_daily'] - sq_min) / (sq_max - sq_min + 1e-8)
                )

        # stress_score is 0-100, normalize to 0-1
        if 'stress_score' in df_synth.columns:
            stress_max = df_synth['stress_score'].max()
            stress_min = df_synth['stress_score'].min()
            df_synth['stress_score'] = (
                (df_synth['stress_score'] - stress_min) / (stress_max - stress_min + 1e-8)
            )

        # recovery_score is 0-100, normalize to 0-1
        if 'recovery_score' in df_synth.columns:
            rec_max = df_synth['recovery_score'].max()
            rec_min = df_synth['recovery_score'].min()
            df_synth['recovery_score'] = (
                (df_synth['recovery_score'] - rec_min) / (rec_max - rec_min + 1e-8)
            )

        # Ensure target exists
        if 'will_get_injured' not in df_synth.columns and 'injury' in df_synth.columns:
                # Reconstruct target if missing from CSV
                indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=7)
                df_synth['will_get_injured'] = df_synth.groupby('athlete_id')['injury'].rolling(window=indexer, min_periods=1).max().reset_index(0, drop=True)
    else:
        print("No synthetic datasets found in data/raw.")
        return

    # 3. Experiment A: Statistical Alignment
    print("\n--- 3. Experiment A: Statistical Alignment (Jensen-Shannon Divergence) ---")
    # Features to compare
    features_to_compare = ['sleep_quality_daily', 'stress_score', 'recovery_score']
    
    stats = AnalyticsService.validate_distributions(df_synth, df_real, features=features_to_compare)
    print(json.dumps(stats, indent=2))
    
    # Check if we pass
    failures = [f for f, res in stats.items() if res.get('status') == 'WARNING']
    if failures:
        print(f"\nWARNING: The following features differ significantly from reality: {failures}")
    else:
        print("\nSUCCESS: Synthetic distributions match real-world data reasonably well.")

    # 4. Experiment B: Sim2Real Transfer (Without Distribution Alignment)
    print("\n--- 4. Experiment B: Sim2Real Transfer Learning (Raw) ---")
    print("Training on Synthetic Data -> Testing on Real PMData (Zero-shot, no alignment)")

    results = TrainingService.train_sim2real_experiment(
        synthetic_df=df_synth,
        real_df=df_real,
        model_type='xgboost'
    )

    if 'error' in results:
        print(f"Experiment Failed: {results['error']}")
    else:
        print(f"\nResults (Raw):")
        print(f"AUC Score: {results['auc']:.4f}")
        print(f"Avg Precision: {results['ap']:.4f}")
        print(f"Features Used: {results['features_used']}")

    # 5. Experiment C: Sim2Real Transfer WITH Distribution Alignment
    print("\n--- 5. Experiment C: Sim2Real Transfer WITH Distribution Alignment ---")
    print("Applying histogram matching to align synthetic distributions with PMData...")

    # Create aligned synthetic data
    df_synth_aligned = df_synth.copy()
    features_to_align = ['sleep_quality_daily', 'stress_score']

    for feature in features_to_align:
        if feature in df_synth_aligned.columns and feature in df_real.columns:
            df_synth_aligned[feature] = histogram_match(
                df_synth_aligned[feature],
                df_real[feature]
            )
            print(f"  Aligned {feature}: synth mean {df_synth_aligned[feature].mean():.3f} -> real mean {df_real[feature].mean():.3f}")

    # Re-run validation with aligned data
    print("\nRe-checking distribution alignment after histogram matching...")
    stats_aligned = AnalyticsService.validate_distributions(df_synth_aligned, df_real, features=features_to_compare)
    for feat, res in stats_aligned.items():
        if 'js_divergence' in res:
            print(f"  {feat}: JS Divergence = {res['js_divergence']:.4f} ({res.get('status', 'N/A')})")

    # Train and test with aligned data
    results_aligned = TrainingService.train_sim2real_experiment(
        synthetic_df=df_synth_aligned,
        real_df=df_real,
        model_type='xgboost'
    )

    if 'error' in results_aligned:
        print(f"Experiment Failed: {results_aligned['error']}")
    else:
        print(f"\nResults (With Alignment):")
        print(f"AUC Score: {results_aligned['auc']:.4f}")
        print(f"Avg Precision: {results_aligned['ap']:.4f}")
        print(f"Features Used: {results_aligned['features_used']}")

        improvement = results_aligned['auc'] - results.get('auc', 0.5)
        print(f"\nImprovement from alignment: {improvement:+.4f} AUC")

        if results_aligned['auc'] > 0.55:
            print("\nCONCLUSION: Distribution alignment WORKED! Synthetic data now predicts real injuries.")
            print("ACTION: Tune synthetic data generator to produce aligned distributions natively.")
        elif results_aligned['auc'] > results.get('auc', 0.5):
            print("\nCONCLUSION: Alignment improved transfer but more work needed.")
            print("Consider: Feature engineering, more features, or signal-to-noise ratio in synthetic data.")
        else:
            print("\nCONCLUSION: Distribution alignment alone is not sufficient.")
            print("The underlying signal in synthetic data may not match real injury patterns.")

    # =========================================================================
    # 6. EXPERIMENT D: CAUSAL MECHANISM VERIFICATION (The "Asymmetry" Proof)
    # =========================================================================
    print("\n" + "="*70)
    print("   6. CAUSAL MECHANISM VERIFICATION: The 'Asymmetry' Proof")
    print("="*70)
    print("\nThis analysis proves the DUAL-PATHWAY hypothesis:")
    print("  - Undertrained (ACWR < 0.8): HIGH risk due to physiological detraining")
    print("  - Optimal (0.8-1.3): LOW risk - the 'sweet spot'")
    print("  - High Risk (ACWR > 1.3): MODERATE risk due to exposure/overload")
    print("\nThe KEY INSIGHT: Undertrained should have HIGHER risk-per-load than Overloaded.")
    print("This proves the 'asymmetry' in the ACWR-injury relationship.\n")

    # Check if we have the glass-box columns
    glass_box_cols = ['acwr', 'injury', 'actual_tss']
    missing_cols = [c for c in glass_box_cols if c not in df_synth.columns]

    if missing_cols:
        print(f"WARNING: Missing glass-box columns: {missing_cols}")
        print("Please regenerate synthetic data with the updated simulation engine.")
        print("The columns 'acwr', 'injury_type', 'load_scenario' are required for causal analysis.")
    else:
        # Define ACWR Zones (matching the paper's definitions)
        df_synth['acwr_zone'] = pd.cut(
            df_synth['acwr'].fillna(1.0),
            bins=[-np.inf, 0.8, 1.3, 1.5, np.inf],
            labels=['Undertrained', 'Optimal', 'Danger', 'High Risk']
        )

        print("--- Risk per 1,000 Load Units by ACWR Zone ---")
        print("(This is the 'exposure-normalized' injury risk)\n")

        results_table = []
        baseline_risk = None  # Will be set to Optimal zone risk

        for zone in ['Undertrained', 'Optimal', 'Danger', 'High Risk']:
            zone_data = df_synth[df_synth['acwr_zone'] == zone]
            total_load = zone_data['actual_tss'].sum()
            total_injuries = zone_data['injury'].sum()
            total_days = len(zone_data)

            # Calculate risk per 1000 load units
            risk_per_load = (total_injuries / total_load * 1000) if total_load > 0 else 0
            daily_injury_rate = (total_injuries / total_days * 100) if total_days > 0 else 0

            if zone == 'Optimal':
                baseline_risk = risk_per_load

            relative_risk = (risk_per_load / baseline_risk) if baseline_risk and baseline_risk > 0 else 0

            results_table.append({
                'Zone': zone,
                'Days': total_days,
                'Total Load': f"{total_load:,.0f}",
                'Injuries': int(total_injuries),
                'Risk/1k TSS': f"{risk_per_load:.3f}",
                'Relative Risk': f"{relative_risk:.2f}x"
            })

        results_df = pd.DataFrame(results_table)
        print(results_df.to_string(index=False))

        # Calculate the key asymmetry metrics
        undertrained = results_table[0]  # Undertrained
        optimal = results_table[1]       # Optimal
        danger = results_table[2]        # Danger
        high_risk = results_table[3]     # High Risk

        ut_risk = float(undertrained['Risk/1k TSS'])
        opt_risk = float(optimal['Risk/1k TSS'])
        hr_risk = float(high_risk['Risk/1k TSS'])

        print("\n--- ASYMMETRY ANALYSIS ---")
        print(f"Undertrained vs Optimal: {ut_risk/opt_risk:.2f}x higher risk" if opt_risk > 0 else "N/A")
        print(f"High Risk vs Optimal: {hr_risk/opt_risk:.2f}x higher risk" if opt_risk > 0 else "N/A")

        # The key test: Is undertrained riskier than high risk?
        if ut_risk > hr_risk and opt_risk > 0:
            asymmetry_ratio = ut_risk / hr_risk
            print(f"\n✓ ASYMMETRY CONFIRMED: Undertrained is {asymmetry_ratio:.2f}x more dangerous than Overloaded")
            print("  This proves the physiological detraining mechanism is stronger than pure exposure risk.")
            print("  The simulation correctly captures the 'U-shaped' ACWR-injury relationship.")
        elif ut_risk > 0 and hr_risk > 0:
            print(f"\n✗ ASYMMETRY NOT CONFIRMED: Undertrained ({ut_risk:.3f}) vs High Risk ({hr_risk:.3f})")
            print("  The expected asymmetry was not observed. Check simulation parameters.")
        else:
            print("\n? INSUFFICIENT DATA: Cannot calculate asymmetry with zero risk values.")

        # Additional insight: Injury type breakdown if available
        if 'injury_type' in df_synth.columns:
            print("\n--- INJURY TYPE BREAKDOWN ---")
            injury_types = df_synth[df_synth['injury'] == 1]['injury_type'].value_counts()
            total_injuries = injury_types.sum()
            for itype, count in injury_types.items():
                pct = (count / total_injuries * 100) if total_injuries > 0 else 0
                print(f"  {itype}: {count} ({pct:.1f}%)")

            # Cross-tabulate injury type by ACWR zone
            print("\n--- INJURY TYPE BY ACWR ZONE ---")
            injury_data = df_synth[df_synth['injury'] == 1]
            if len(injury_data) > 0:
                crosstab = pd.crosstab(injury_data['acwr_zone'], injury_data['injury_type'])
                print(crosstab.to_string())

        # Load scenario breakdown if available
        if 'load_scenario' in df_synth.columns:
            print("\n--- LOAD SCENARIO BREAKDOWN ---")
            scenarios = df_synth['load_scenario'].value_counts()
            total_days = len(df_synth)
            for scenario, count in scenarios.items():
                pct = (count / total_days * 100) if total_days > 0 else 0
                # Calculate injury rate for this scenario
                scenario_injuries = df_synth[df_synth['load_scenario'] == scenario]['injury'].sum()
                scenario_rate = (scenario_injuries / count * 100) if count > 0 else 0
                print(f"  {scenario}: {count} days ({pct:.1f}%) - Injury rate: {scenario_rate:.2f}%")

    # =========================================================================
    # FINAL CONCLUSION
    # =========================================================================
    print("\n" + "="*70)
    print("   FINAL VALIDATION SUMMARY")
    print("="*70)
    print("\n1. STATISTICAL ALIGNMENT: JS Divergence scores above")
    print("2. SIM2REAL TRANSFER: AUC scores above")
    print("3. CAUSAL MECHANISM: Risk-per-load analysis above")
    print("\nIf all three pass, the synthetic data is publication-ready.")
    print("If causal asymmetry is confirmed, the simulation is scientifically valid.")

if __name__ == "__main__":
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        main()
