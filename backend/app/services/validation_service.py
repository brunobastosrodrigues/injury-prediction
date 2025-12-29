"""
Validation Service for Sim2Real experiments.

Provides methods to compare synthetic data against real PMData,
calculate distribution alignment, and run transfer learning experiments.
"""

import os
import glob
import pandas as pd
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon
from typing import Dict, List, Any, Optional

from .pm_adapter import PMDataAdapter
from .training_service import TrainingService


class ValidationService:
    """Service for Sim2Real validation experiments."""

    @classmethod
    def get_pmdata_path(cls) -> str:
        """Get the PMData directory path."""
        from flask import current_app
        # Try multiple paths (Docker mounts data at /data)
        possible_paths = [
            '/data/external/pmdata',  # Docker volume mount
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'external', 'pmdata'),
            os.path.join(os.path.dirname(current_app.root_path), 'data', 'external', 'pmdata'),
            '/home/rodrigues/injury-prediction/data/external/pmdata',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]

    @classmethod
    def get_synthetic_path(cls) -> Optional[str]:
        """Get the latest synthetic dataset path."""
        from flask import current_app
        # Try multiple paths (Docker mounts data at /data)
        possible_paths = [
            '/data/raw',  # Docker volume mount
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'raw'),
            os.path.join(os.path.dirname(current_app.root_path), 'data', 'raw'),
            '/home/rodrigues/injury-prediction/data/raw',
        ]
        raw_path = None
        for path in possible_paths:
            if os.path.exists(path):
                raw_path = path
                break
        if not raw_path:
            return None

        # Prefer calibrated dataset
        calibrated = os.path.join(raw_path, 'dataset_pmdata_calibrated')
        if os.path.exists(calibrated):
            return calibrated

        # Otherwise use latest
        datasets = sorted(glob.glob(os.path.join(raw_path, 'dataset_*')))
        return datasets[-1] if datasets else None

    @classmethod
    def load_pmdata(cls) -> Optional[pd.DataFrame]:
        """Load and standardize PMData."""
        pmdata_path = cls.get_pmdata_path()
        if not os.path.exists(pmdata_path):
            return None

        try:
            adapter = PMDataAdapter(pmdata_path)
            return adapter.load_and_unify()
        except Exception as e:
            print(f"Error loading PMData: {e}")
            return None

    @classmethod
    def load_synthetic(cls) -> Optional[pd.DataFrame]:
        """Load synthetic dataset."""
        synth_path = cls.get_synthetic_path()
        if not synth_path:
            return None

        try:
            # Try parquet first, then CSV
            parquet_path = os.path.join(synth_path, 'daily_data.parquet')
            csv_path = os.path.join(synth_path, 'daily_data.csv')

            if os.path.exists(parquet_path):
                df = pd.read_parquet(parquet_path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                return None

            # Rename columns to match PMData schema
            rename_map = {
                'sleep_quality': 'sleep_quality_daily',
                'stress': 'stress_score',
                'body_battery_morning': 'recovery_score'
            }
            df = df.rename(columns=rename_map)

            # Normalize to 0-1
            for col in ['sleep_quality_daily', 'stress_score', 'recovery_score', 'sleep_hours']:
                if col in df.columns:
                    col_min, col_max = df[col].min(), df[col].max()
                    if col_max > col_min:
                        df[col] = (df[col] - col_min) / (col_max - col_min)

            return df
        except Exception as e:
            print(f"Error loading synthetic data: {e}")
            return None

    @classmethod
    def calculate_js_divergence(cls, arr1: np.ndarray, arr2: np.ndarray, bins: int = 50) -> float:
        """Calculate Jensen-Shannon divergence between two arrays."""
        # Create histograms with same bins
        min_val = min(arr1.min(), arr2.min())
        max_val = max(arr1.max(), arr2.max())
        bins_edges = np.linspace(min_val, max_val, bins + 1)

        hist1, _ = np.histogram(arr1, bins=bins_edges, density=True)
        hist2, _ = np.histogram(arr2, bins=bins_edges, density=True)

        # Add small epsilon to avoid division by zero
        hist1 = hist1 + 1e-10
        hist2 = hist2 + 1e-10

        # Normalize
        hist1 = hist1 / hist1.sum()
        hist2 = hist2 / hist2.sum()

        return float(jensenshannon(hist1, hist2))

    @classmethod
    def get_distribution_comparison(cls) -> Dict[str, Any]:
        """
        Compare distributions between synthetic and real data.

        Returns JS divergence and distribution stats for each feature.
        """
        df_synth = cls.load_synthetic()
        df_real = cls.load_pmdata()

        if df_synth is None:
            return {'error': 'No synthetic data found', 'has_synthetic': False}
        if df_real is None:
            return {'error': 'No PMData found', 'has_pmdata': False}

        # Compare wellness features (both datasets have these)
        wellness_features = ['sleep_quality_daily', 'stress_score', 'recovery_score', 'sleep_hours']
        # Load features (only PMData has these currently)
        load_features = ['daily_load', 'acute_load', 'chronic_load', 'acwr']
        features = wellness_features
        results = {
            'has_synthetic': True,
            'has_pmdata': True,
            'synthetic_samples': len(df_synth),
            'real_samples': len(df_real),
            'features': {}
        }

        for feat in features:
            if feat not in df_synth.columns or feat not in df_real.columns:
                results['features'][feat] = {'error': 'Column missing'}
                continue

            synth_vals = df_synth[feat].dropna().values
            real_vals = df_real[feat].dropna().values

            js_div = cls.calculate_js_divergence(synth_vals, real_vals)

            # Create histogram data for charts
            bins = np.linspace(0, 1, 21)  # 20 bins from 0 to 1
            synth_hist, _ = np.histogram(synth_vals, bins=bins, density=True)
            real_hist, _ = np.histogram(real_vals, bins=bins, density=True)

            results['features'][feat] = {
                'js_divergence': round(js_div, 4),
                'status': 'PASS' if js_div < 0.1 else 'WARNING' if js_div < 0.3 else 'FAIL',
                'synthetic': {
                    'mean': round(float(synth_vals.mean()), 4),
                    'std': round(float(synth_vals.std()), 4),
                    'min': round(float(synth_vals.min()), 4),
                    'max': round(float(synth_vals.max()), 4),
                    'histogram': synth_hist.tolist()
                },
                'real': {
                    'mean': round(float(real_vals.mean()), 4),
                    'std': round(float(real_vals.std()), 4),
                    'min': round(float(real_vals.min()), 4),
                    'max': round(float(real_vals.max()), 4),
                    'histogram': real_hist.tolist()
                },
                'bins': bins.tolist()
            }

        # Add load feature statistics from PMData (not compared with synthetic yet)
        results['load_features'] = {}
        for feat in load_features:
            if feat in df_real.columns:
                vals = df_real[feat].dropna().values
                if len(vals) > 0:
                    results['load_features'][feat] = {
                        'mean': round(float(vals.mean()), 4),
                        'std': round(float(vals.std()), 4),
                        'min': round(float(vals.min()), 4),
                        'max': round(float(vals.max()), 4),
                        'count': len(vals)
                    }

        # Add ACWR zone analysis
        if 'acwr' in df_real.columns and 'will_get_injured' in df_real.columns:
            def get_zone(x):
                if pd.isna(x):
                    return 'unknown'
                elif x < 0.8:
                    return 'undertrained (<0.8)'
                elif x < 1.3:
                    return 'optimal (0.8-1.3)'
                elif x < 1.5:
                    return 'danger (1.3-1.5)'
                else:
                    return 'high risk (>1.5)'

            df_real['acwr_zone'] = df_real['acwr'].apply(get_zone)
            zone_stats = df_real.groupby('acwr_zone')['will_get_injured'].agg(['mean', 'count'])
            results['acwr_zones'] = {
                zone: {'injury_rate': round(float(row['mean']), 4), 'count': int(row['count'])}
                for zone, row in zone_stats.iterrows() if zone != 'unknown'
            }

        return results

    @classmethod
    def run_sim2real_experiment(cls) -> Dict[str, Any]:
        """
        Run Sim2Real transfer learning experiment.

        Trains on synthetic data, tests on real PMData.
        """
        df_synth = cls.load_synthetic()
        df_real = cls.load_pmdata()

        if df_synth is None:
            return {'error': 'No synthetic data found'}
        if df_real is None:
            return {'error': 'No PMData found'}

        # Ensure target exists in synthetic
        if 'will_get_injured' not in df_synth.columns and 'injury' in df_synth.columns:
            indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=7)
            df_synth['will_get_injured'] = df_synth.groupby('athlete_id')['injury'].rolling(
                window=indexer, min_periods=1
            ).max().reset_index(0, drop=True)

        # Run experiment
        results = TrainingService.train_sim2real_experiment(
            synthetic_df=df_synth,
            real_df=df_real,
            model_type='xgboost'
        )

        if 'error' in results:
            return results

        # Add interpretation
        auc = results.get('auc', 0.5)
        if auc > 0.6:
            interpretation = 'Good transfer - synthetic data captures real injury patterns'
            status = 'success'
        elif auc > 0.55:
            interpretation = 'Moderate transfer - some signal transfers from simulation'
            status = 'warning'
        else:
            interpretation = 'Poor transfer - synthetic patterns do not match real data'
            status = 'error'

        results['interpretation'] = interpretation
        results['status'] = status

        return results

    @classmethod
    def get_pmdata_analysis(cls) -> Dict[str, Any]:
        """
        Analyze PMData to understand real injury patterns.

        Returns correlations and feature importance.
        """
        df = cls.load_pmdata()
        if df is None:
            return {'error': 'No PMData found'}

        target = 'will_get_injured'
        feature_cols = [c for c in df.columns if c not in ['date', 'athlete_id', 'is_injured', 'will_get_injured']]

        # Calculate correlations
        correlations = []
        for feat in feature_cols:
            if feat in df.columns:
                try:
                    # Drop NaN values for correlation calculation
                    valid_mask = df[feat].notna() & df[target].notna()
                    feat_vals = df.loc[valid_mask, feat]
                    target_vals = df.loc[valid_mask, target]

                    # Skip if not enough valid data or constant values
                    if len(feat_vals) < 10 or feat_vals.std() == 0:
                        continue

                    spearman_r, spearman_p = stats.spearmanr(feat_vals, target_vals)

                    # Skip if correlation is NaN
                    if np.isnan(spearman_r) or np.isnan(spearman_p):
                        continue

                    correlations.append({
                        'feature': feat,
                        'correlation': round(float(spearman_r), 4),
                        'p_value': round(float(spearman_p), 4),
                        'significant': bool(spearman_p < 0.05),
                        'direction': 'increases risk' if spearman_r > 0 else 'decreases risk'
                    })
                except (ValueError, TypeError, FloatingPointError):
                    pass

        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

        # Calculate injury signature (Safe vs Pre-Injury)
        safe_days = df[df[target] == 0]
        preinjury_days = df[df[target] == 1]

        signature = []
        for feat in feature_cols:
            if feat in df.columns:
                try:
                    safe_mean = safe_days[feat].mean()
                    preinjury_mean = preinjury_days[feat].mean()

                    # Skip if either mean is NaN
                    if np.isnan(safe_mean) or np.isnan(preinjury_mean):
                        continue

                    delta_pct = ((preinjury_mean - safe_mean) / (safe_mean + 1e-8)) * 100
                    signature.append({
                        'feature': feat,
                        'safe_mean': round(float(safe_mean), 4),
                        'preinjury_mean': round(float(preinjury_mean), 4),
                        'delta_percent': round(float(delta_pct), 2),
                        'direction': 'increases' if delta_pct > 0 else 'decreases'
                    })
                except (ValueError, TypeError, FloatingPointError):
                    pass

        signature.sort(key=lambda x: abs(x['delta_percent']), reverse=True)

        # Train RF for feature importance
        from sklearn.ensemble import RandomForestClassifier

        X = df[feature_cols].dropna()
        y = df.loc[X.index, target]

        rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
        rf.fit(X, y)

        importance = []
        for feat, imp in zip(feature_cols, rf.feature_importances_):
            importance.append({
                'feature': feat,
                'importance': round(float(imp), 4)
            })

        importance.sort(key=lambda x: x['importance'], reverse=True)

        return {
            'samples': len(df),
            'injury_rate': round(float(df[target].mean()), 4),
            'safe_days': int((df[target] == 0).sum()),
            'preinjury_days': int((df[target] == 1).sum()),
            'correlations': correlations,
            'injury_signature': signature,
            'feature_importance': importance
        }

    @classmethod
    def evaluate_pmdata_model(cls) -> Dict[str, Any]:
        """
        Train and evaluate an XGBoost model on PMData with load features.

        This tests whether load features (ACWR) improve injury prediction.
        """
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score, classification_report
        import xgboost as xgb

        df = cls.load_pmdata()
        if df is None:
            return {'error': 'No PMData found'}

        target = 'will_get_injured'

        # Define feature sets
        wellness_features = ['sleep_quality_daily', 'stress_score', 'recovery_score',
                             'fatigue_score', 'mood_score', 'soreness_score', 'sleep_hours']
        load_features = ['daily_load', 'acute_load', 'chronic_load', 'acwr',
                         'daily_load_norm', 'acute_load_norm', 'chronic_load_norm']

        # Filter to available features
        available_wellness = [f for f in wellness_features if f in df.columns]
        available_load = [f for f in load_features if f in df.columns]

        results = {'wellness_only': {}, 'load_only': {}, 'combined': {}}

        # Train 3 models: wellness-only, load-only, combined
        for name, features in [
            ('wellness_only', available_wellness),
            ('load_only', available_load),
            ('combined', available_wellness + available_load)
        ]:
            if not features:
                results[name] = {'error': 'No features available'}
                continue

            # Prepare data
            df_clean = df.dropna(subset=features + [target])
            if len(df_clean) < 100:
                results[name] = {'error': f'Insufficient data: {len(df_clean)} samples'}
                continue

            X = df_clean[features]
            y = df_clean[target]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )

            # Train XGBoost
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)

            # Evaluate
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)

            # Feature importance
            importance = sorted(
                zip(features, model.feature_importances_),
                key=lambda x: x[1], reverse=True
            )

            results[name] = {
                'auc': round(float(auc), 4),
                'samples': len(df_clean),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'features': features,
                'feature_importance': [
                    {'feature': f, 'importance': round(float(i), 4)}
                    for f, i in importance[:10]
                ]
            }

        # Calculate improvement
        if 'auc' in results['wellness_only'] and 'auc' in results['combined']:
            wellness_auc = results['wellness_only']['auc']
            combined_auc = results['combined']['auc']
            improvement = combined_auc - wellness_auc
            results['improvement'] = {
                'absolute': round(improvement, 4),
                'relative_pct': round(improvement / max(wellness_auc, 0.01) * 100, 2),
                'conclusion': 'Load features improve prediction' if improvement > 0.02 else 'Marginal improvement'
            }

        return results

    @classmethod
    def get_validation_summary(cls) -> Dict[str, Any]:
        """Get a summary of all validation metrics."""
        distributions = cls.get_distribution_comparison()
        sim2real = cls.run_sim2real_experiment()
        pmdata = cls.get_pmdata_analysis()
        model_eval = cls.evaluate_pmdata_model()

        # Calculate overall score
        if 'features' in distributions:
            js_scores = [f['js_divergence'] for f in distributions['features'].values() if 'js_divergence' in f]
            avg_js = sum(js_scores) / len(js_scores) if js_scores else 1.0
        else:
            avg_js = 1.0

        auc = sim2real.get('auc', 0.5)

        # Combined score (lower JS + higher AUC = better)
        alignment_score = max(0, 1 - avg_js)  # 0-1, higher is better
        transfer_score = max(0, (auc - 0.5) * 2)  # 0-1, higher is better
        overall_score = (alignment_score * 0.4 + transfer_score * 0.6)

        # Use load model AUC if better than sim2real
        load_auc = model_eval.get('combined', {}).get('auc', 0.5)

        return {
            'overall_score': round(overall_score, 2),
            'alignment_score': round(alignment_score, 2),
            'transfer_score': round(transfer_score, 2),
            'avg_js_divergence': round(avg_js, 4),
            'sim2real_auc': round(auc, 4),
            'pmdata_model_auc': round(load_auc, 4),
            'distributions': distributions,
            'sim2real': sim2real,
            'pmdata_analysis': pmdata,
            'model_evaluation': model_eval
        }

    # =========================================================================
    # CAUSAL MECHANISM ANALYSIS (For Publication)
    # =========================================================================

    @classmethod
    def get_causal_mechanism_analysis(cls) -> Dict[str, Any]:
        """
        Comprehensive causal mechanism analysis for synthetic data.

        Validates the "Asymmetric ACWR" hypothesis and provides
        publication-quality metrics for the Three Pillars of Validity:
        1. Statistical Fidelity
        2. Causal Fidelity
        3. Transferability
        """
        from ..utils.publication_plots import (
            calculate_causal_asymmetry,
            calculate_risk_landscape,
            calculate_wellness_vulnerability_analysis,
            calculate_load_scenario_analysis,
            calculate_injury_type_breakdown
        )

        df_synth = cls.load_synthetic_raw()  # Load with glass-box columns

        if df_synth is None:
            return {'error': 'No synthetic data found. Generate a cohort first.'}

        results = {
            'has_data': True,
            'total_samples': len(df_synth),
            'total_athletes': df_synth['athlete_id'].nunique() if 'athlete_id' in df_synth.columns else 0
        }

        # 1. Causal Asymmetry Analysis (The Paper's Main Finding)
        if 'acwr' in df_synth.columns:
            results['causal_asymmetry'] = calculate_causal_asymmetry(
                df_synth,
                acwr_col='acwr',
                injury_col='injury',
                load_col='actual_tss'
            )
        else:
            results['causal_asymmetry'] = {'error': 'ACWR column not found - regenerate data with glass-box columns'}

        # 2. Risk Landscape (Contour plot data)
        if 'actual_tss' in df_synth.columns:
            results['risk_landscape'] = calculate_risk_landscape(
                df_synth,
                injury_col='injury'
            )
        else:
            results['risk_landscape'] = {'error': 'Load data not found'}

        # 3. Wellness Vulnerability Analysis
        if 'wellness_vulnerability' in df_synth.columns:
            results['wellness_vulnerability'] = calculate_wellness_vulnerability_analysis(
                df_synth,
                wellness_col='wellness_vulnerability',
                injury_col='injury'
            )
        else:
            results['wellness_vulnerability'] = {'error': 'Wellness vulnerability not found - regenerate with glass-box columns'}

        # 4. Load Scenario Analysis
        if 'load_scenario' in df_synth.columns:
            results['load_scenarios'] = calculate_load_scenario_analysis(
                df_synth,
                scenario_col='load_scenario',
                injury_col='injury'
            )
        else:
            results['load_scenarios'] = {'error': 'Load scenario not found'}

        # 5. Injury Type Breakdown
        if 'injury_type' in df_synth.columns:
            results['injury_types'] = calculate_injury_type_breakdown(
                df_synth,
                injury_type_col='injury_type',
                injury_col='injury'
            )
        else:
            results['injury_types'] = {'error': 'Injury type not found'}

        # 6. Overall injury statistics
        if 'injury' in df_synth.columns:
            injury_days = df_synth['injury'].sum()
            total_days = len(df_synth)
            results['injury_statistics'] = {
                'total_injury_days': int(injury_days),
                'total_days': int(total_days),
                'injury_rate_pct': round(injury_days / total_days * 100, 2) if total_days > 0 else 0,
                'injuries_per_athlete': round(injury_days / results['total_athletes'], 2) if results['total_athletes'] > 0 else 0
            }

        return results

    @classmethod
    def load_synthetic_raw(cls) -> Optional[pd.DataFrame]:
        """Load synthetic dataset with all glass-box columns (no renaming)."""
        synth_path = cls.get_synthetic_path()
        if not synth_path:
            return None

        try:
            parquet_path = os.path.join(synth_path, 'daily_data.parquet')
            csv_path = os.path.join(synth_path, 'daily_data.csv')

            if os.path.exists(parquet_path):
                return pd.read_parquet(parquet_path)
            elif os.path.exists(csv_path):
                return pd.read_csv(csv_path)
            else:
                return None
        except Exception as e:
            print(f"Error loading synthetic data: {e}")
            return None

    @classmethod
    def get_raincloud_data(cls, feature: str) -> Dict[str, Any]:
        """
        Get data for raincloud plot comparing synthetic vs real distributions.
        """
        from ..utils.publication_plots import calculate_raincloud_data

        df_synth = cls.load_synthetic()
        df_real = cls.load_pmdata()

        if df_synth is None:
            return {'error': 'No synthetic data found'}
        if df_real is None:
            return {'error': 'No PMData found'}

        return calculate_raincloud_data(df_synth, df_real, feature)

    @classmethod
    def get_three_pillars_summary(cls) -> Dict[str, Any]:
        """
        Get a summary aligned with the Three Pillars of Validity framework.

        1. Statistical Fidelity: JS Divergence < 0.1 for wellness features
        2. Causal Fidelity: Undertrained zone shows 2-3x higher risk per load
        3. Transferability: Sim2Real AUC > 0.60
        """
        results = {
            'pillars': {
                'statistical_fidelity': {'status': 'pending', 'score': 0},
                'causal_fidelity': {'status': 'pending', 'score': 0},
                'transferability': {'status': 'pending', 'score': 0}
            }
        }

        # 1. Statistical Fidelity
        try:
            distributions = cls.get_distribution_comparison()
            if 'features' in distributions:
                js_scores = [
                    f.get('js_divergence', 1.0)
                    for f in distributions['features'].values()
                    if isinstance(f, dict) and 'js_divergence' in f
                ]
                if js_scores:
                    avg_js = sum(js_scores) / len(js_scores)
                    passing = sum(1 for js in js_scores if js < 0.1)

                    results['pillars']['statistical_fidelity'] = {
                        'status': 'pass' if avg_js < 0.1 else 'warning' if avg_js < 0.2 else 'fail',
                        'score': round(max(0, 1 - avg_js), 2),
                        'avg_js_divergence': round(avg_js, 4),
                        'features_passing': f'{passing}/{len(js_scores)}',
                        'target': 'JS < 0.1 for all features'
                    }
        except Exception as e:
            results['pillars']['statistical_fidelity']['error'] = str(e)

        # 2. Causal Fidelity
        try:
            causal = cls.get_causal_mechanism_analysis()
            if 'causal_asymmetry' in causal and 'summary' in causal['causal_asymmetry']:
                summary = causal['causal_asymmetry']['summary']
                ut_ratio = summary.get('undertrained_vs_optimal', 0)
                hr_ratio = summary.get('high_risk_vs_optimal', 0)

                # Good: undertrained > 1.5x and > high_risk (proves physiological mechanism)
                is_asymmetric = ut_ratio > hr_ratio and ut_ratio > 1.5

                results['pillars']['causal_fidelity'] = {
                    'status': 'pass' if is_asymmetric else 'warning' if ut_ratio > 1.2 else 'fail',
                    'score': round(min(1.0, ut_ratio / 3.0), 2),  # Score based on undertrained ratio
                    'undertrained_risk_ratio': ut_ratio,
                    'high_risk_ratio': hr_ratio,
                    'is_asymmetric': is_asymmetric,
                    'target': 'Undertrained zone shows 2-3x higher risk per load unit',
                    'interpretation': summary.get('interpretation', '')
                }
        except Exception as e:
            results['pillars']['causal_fidelity']['error'] = str(e)

        # 3. Transferability
        try:
            sim2real = cls.run_sim2real_experiment()
            auc = sim2real.get('auc', 0.5)

            results['pillars']['transferability'] = {
                'status': 'pass' if auc > 0.60 else 'warning' if auc > 0.55 else 'fail',
                'score': round(max(0, (auc - 0.5) * 2), 2),
                'sim2real_auc': round(auc, 4),
                'target': 'Sim2Real AUC > 0.60',
                'interpretation': sim2real.get('interpretation', '')
            }
        except Exception as e:
            results['pillars']['transferability']['error'] = str(e)

        # Overall assessment
        scores = [
            p.get('score', 0)
            for p in results['pillars'].values()
            if isinstance(p, dict) and 'score' in p
        ]
        results['overall_score'] = round(sum(scores) / len(scores), 2) if scores else 0

        passing = sum(1 for p in results['pillars'].values() if p.get('status') == 'pass')
        results['pillars_passing'] = f'{passing}/3'
        results['ready_for_publication'] = passing == 3

        return results

    # =========================================================================
    # DATASET-SPECIFIC METHODS (For Async Validation)
    # =========================================================================

    @classmethod
    def get_validation_cache_dir(cls) -> str:
        """Get the validation cache directory path."""
        from flask import current_app
        possible_paths = [
            '/data/validation',
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'validation'),
            '/home/rodrigues/injury-prediction/data/validation',
        ]
        for path in possible_paths:
            parent = os.path.dirname(path)
            if os.path.exists(parent):
                os.makedirs(path, exist_ok=True)
                return path
        return possible_paths[0]

    @classmethod
    def get_cached_results(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Load cached validation results for a dataset."""
        import json
        cache_dir = os.path.join(cls.get_validation_cache_dir(), dataset_id)
        summary_path = os.path.join(cache_dir, 'summary.json')

        if not os.path.exists(summary_path):
            return None

        try:
            results = {'dataset_id': dataset_id}
            files = ['summary.json', 'distributions.json', 'sim2real.json',
                     'pmdata_analysis.json', 'causal_mechanism.json', 'three_pillars.json']

            for filename in files:
                filepath = os.path.join(cache_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        key = filename.replace('.json', '')
                        results[key] = json.load(f)

            return results
        except Exception as e:
            print(f"Error loading cached results: {e}")
            return None

    @classmethod
    def list_cached_validations(cls) -> List[Dict[str, Any]]:
        """List all datasets with cached validation results."""
        import json
        cache_dir = cls.get_validation_cache_dir()
        validations = []

        if not os.path.exists(cache_dir):
            return validations

        for dataset_id in os.listdir(cache_dir):
            summary_path = os.path.join(cache_dir, dataset_id, 'summary.json')
            if os.path.exists(summary_path):
                try:
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)
                        validations.append({
                            'dataset_id': dataset_id,
                            'computed_at': summary.get('computed_at'),
                            'overall_score': summary.get('overall_score', 0),
                            'pillars_passing': summary.get('pillars_passing', '0/3'),
                            'ready_for_publication': summary.get('ready_for_publication', False),
                            'sim2real_auc': summary.get('sim2real_auc', 0),
                        })
                except Exception:
                    pass

        return sorted(validations, key=lambda x: x.get('computed_at', ''), reverse=True)

    @classmethod
    def delete_cached_results(cls, dataset_id: str) -> bool:
        """Delete cached validation results for a dataset."""
        import shutil
        cache_dir = os.path.join(cls.get_validation_cache_dir(), dataset_id)
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            return True
        return False

    @classmethod
    def load_synthetic_by_id(cls, dataset_id: str) -> Optional[pd.DataFrame]:
        """Load a specific synthetic dataset by ID."""
        from flask import current_app
        possible_paths = [
            f'/data/raw/{dataset_id}',
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'raw', dataset_id),
            f'/home/rodrigues/injury-prediction/data/raw/{dataset_id}',
        ]

        synth_path = None
        for path in possible_paths:
            if os.path.exists(path):
                synth_path = path
                break

        if not synth_path:
            return None

        try:
            parquet_path = os.path.join(synth_path, 'daily_data.parquet')
            csv_path = os.path.join(synth_path, 'daily_data.csv')

            if os.path.exists(parquet_path):
                df = pd.read_parquet(parquet_path)
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                return None

            # Rename columns to match PMData schema
            rename_map = {
                'sleep_quality': 'sleep_quality_daily',
                'stress': 'stress_score',
                'body_battery_morning': 'recovery_score'
            }
            df = df.rename(columns=rename_map)

            # Normalize to 0-1
            for col in ['sleep_quality_daily', 'stress_score', 'recovery_score', 'sleep_hours']:
                if col in df.columns:
                    col_min, col_max = df[col].min(), df[col].max()
                    if col_max > col_min:
                        df[col] = (df[col] - col_min) / (col_max - col_min)

            return df
        except Exception as e:
            print(f"Error loading synthetic dataset {dataset_id}: {e}")
            return None

    @classmethod
    def load_synthetic_raw_by_id(cls, dataset_id: str) -> Optional[pd.DataFrame]:
        """Load a specific synthetic dataset with all glass-box columns (no renaming)."""
        from flask import current_app
        possible_paths = [
            f'/data/raw/{dataset_id}',
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'raw', dataset_id),
            f'/home/rodrigues/injury-prediction/data/raw/{dataset_id}',
        ]

        synth_path = None
        for path in possible_paths:
            if os.path.exists(path):
                synth_path = path
                break

        if not synth_path:
            return None

        try:
            parquet_path = os.path.join(synth_path, 'daily_data.parquet')
            csv_path = os.path.join(synth_path, 'daily_data.csv')

            if os.path.exists(parquet_path):
                return pd.read_parquet(parquet_path)
            elif os.path.exists(csv_path):
                return pd.read_csv(csv_path)
            else:
                return None
        except Exception as e:
            print(f"Error loading synthetic dataset {dataset_id}: {e}")
            return None

    @classmethod
    def get_distribution_comparison_for_dataset(cls, dataset_id: str) -> Dict[str, Any]:
        """Compare distributions between a specific synthetic dataset and real data."""
        df_synth = cls.load_synthetic_by_id(dataset_id)
        df_real = cls.load_pmdata()

        if df_synth is None:
            return {'error': f'Dataset {dataset_id} not found', 'has_synthetic': False}
        if df_real is None:
            return {'error': 'No PMData found', 'has_pmdata': False}

        # Compare wellness features
        wellness_features = ['sleep_quality_daily', 'stress_score', 'recovery_score', 'sleep_hours']
        results = {
            'has_synthetic': True,
            'has_pmdata': True,
            'dataset_id': dataset_id,
            'synthetic_samples': len(df_synth),
            'real_samples': len(df_real),
            'features': {}
        }

        for feat in wellness_features:
            if feat not in df_synth.columns or feat not in df_real.columns:
                results['features'][feat] = {'error': 'Column missing'}
                continue

            synth_vals = df_synth[feat].dropna().values
            real_vals = df_real[feat].dropna().values

            js_div = cls.calculate_js_divergence(synth_vals, real_vals)

            # Create histogram data for charts
            bins = np.linspace(0, 1, 21)
            synth_hist, _ = np.histogram(synth_vals, bins=bins, density=True)
            real_hist, _ = np.histogram(real_vals, bins=bins, density=True)

            results['features'][feat] = {
                'js_divergence': round(js_div, 4),
                'status': 'PASS' if js_div < 0.1 else 'WARNING' if js_div < 0.3 else 'FAIL',
                'synthetic': {
                    'mean': round(float(synth_vals.mean()), 4),
                    'std': round(float(synth_vals.std()), 4),
                    'min': round(float(synth_vals.min()), 4),
                    'max': round(float(synth_vals.max()), 4),
                    'histogram': synth_hist.tolist()
                },
                'real': {
                    'mean': round(float(real_vals.mean()), 4),
                    'std': round(float(real_vals.std()), 4),
                    'min': round(float(real_vals.min()), 4),
                    'max': round(float(real_vals.max()), 4),
                    'histogram': real_hist.tolist()
                },
                'bins': bins.tolist()
            }

        return results

    @classmethod
    def run_sim2real_for_dataset(cls, dataset_id: str) -> Dict[str, Any]:
        """Run Sim2Real transfer learning experiment for a specific dataset."""
        df_synth = cls.load_synthetic_by_id(dataset_id)
        df_real = cls.load_pmdata()

        if df_synth is None:
            return {'error': f'Dataset {dataset_id} not found'}
        if df_real is None:
            return {'error': 'No PMData found'}

        # Ensure target exists in synthetic
        if 'will_get_injured' not in df_synth.columns and 'injury' in df_synth.columns:
            indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=7)
            df_synth['will_get_injured'] = df_synth.groupby('athlete_id')['injury'].rolling(
                window=indexer, min_periods=1
            ).max().reset_index(0, drop=True)

        # Run experiment
        results = TrainingService.train_sim2real_experiment(
            synthetic_df=df_synth,
            real_df=df_real,
            model_type='xgboost'
        )

        if 'error' in results:
            return results

        # Add interpretation
        auc = results.get('auc', 0.5)
        if auc > 0.6:
            interpretation = 'Good transfer - synthetic data captures real injury patterns'
            status = 'success'
        elif auc > 0.55:
            interpretation = 'Moderate transfer - some signal transfers from simulation'
            status = 'warning'
        else:
            interpretation = 'Poor transfer - synthetic patterns do not match real data'
            status = 'error'

        results['interpretation'] = interpretation
        results['status'] = status
        results['dataset_id'] = dataset_id

        return results

    @classmethod
    def get_causal_mechanism_for_dataset(cls, dataset_id: str) -> Dict[str, Any]:
        """Get causal mechanism analysis for a specific dataset."""
        from ..utils.publication_plots import (
            calculate_causal_asymmetry,
            calculate_risk_landscape,
            calculate_wellness_vulnerability_analysis,
            calculate_load_scenario_analysis,
            calculate_injury_type_breakdown
        )

        df_synth = cls.load_synthetic_raw_by_id(dataset_id)

        if df_synth is None:
            return {'error': f'Dataset {dataset_id} not found'}

        results = {
            'has_data': True,
            'dataset_id': dataset_id,
            'total_samples': len(df_synth),
            'total_athletes': df_synth['athlete_id'].nunique() if 'athlete_id' in df_synth.columns else 0
        }

        # 1. Causal Asymmetry Analysis
        if 'acwr' in df_synth.columns:
            results['causal_asymmetry'] = calculate_causal_asymmetry(
                df_synth,
                acwr_col='acwr',
                injury_col='injury',
                load_col='actual_tss'
            )
        else:
            results['causal_asymmetry'] = {'error': 'ACWR column not found'}

        # 2. Risk Landscape
        if 'actual_tss' in df_synth.columns:
            results['risk_landscape'] = calculate_risk_landscape(
                df_synth,
                injury_col='injury'
            )
        else:
            results['risk_landscape'] = {'error': 'Load data not found'}

        # 3. Wellness Vulnerability Analysis
        if 'wellness_vulnerability' in df_synth.columns:
            results['wellness_vulnerability'] = calculate_wellness_vulnerability_analysis(
                df_synth,
                wellness_col='wellness_vulnerability',
                injury_col='injury'
            )
        else:
            results['wellness_vulnerability'] = {'error': 'Wellness vulnerability not found'}

        # 4. Load Scenario Analysis
        if 'load_scenario' in df_synth.columns:
            results['load_scenarios'] = calculate_load_scenario_analysis(
                df_synth,
                scenario_col='load_scenario',
                injury_col='injury'
            )
        else:
            results['load_scenarios'] = {'error': 'Load scenario not found'}

        # 5. Injury Type Breakdown
        if 'injury_type' in df_synth.columns:
            results['injury_types'] = calculate_injury_type_breakdown(
                df_synth,
                injury_type_col='injury_type',
                injury_col='injury'
            )
        else:
            results['injury_types'] = {'error': 'Injury type not found'}

        # 6. Overall injury statistics
        if 'injury' in df_synth.columns:
            injury_days = df_synth['injury'].sum()
            total_days = len(df_synth)
            results['injury_statistics'] = {
                'total_injury_days': int(injury_days),
                'total_days': int(total_days),
                'injury_rate_pct': round(injury_days / total_days * 100, 2) if total_days > 0 else 0,
                'injuries_per_athlete': round(injury_days / results['total_athletes'], 2) if results['total_athletes'] > 0 else 0
            }

        return results

    @classmethod
    def get_three_pillars_for_dataset(cls, dataset_id: str) -> Dict[str, Any]:
        """Get Three Pillars summary for a specific dataset."""
        results = {
            'dataset_id': dataset_id,
            'pillars': {
                'statistical_fidelity': {'status': 'pending', 'score': 0},
                'causal_fidelity': {'status': 'pending', 'score': 0},
                'transferability': {'status': 'pending', 'score': 0}
            }
        }

        # 1. Statistical Fidelity
        try:
            distributions = cls.get_distribution_comparison_for_dataset(dataset_id)
            if 'features' in distributions:
                js_scores = [
                    f.get('js_divergence', 1.0)
                    for f in distributions['features'].values()
                    if isinstance(f, dict) and 'js_divergence' in f
                ]
                if js_scores:
                    avg_js = sum(js_scores) / len(js_scores)
                    passing = sum(1 for js in js_scores if js < 0.1)

                    results['pillars']['statistical_fidelity'] = {
                        'status': 'pass' if avg_js < 0.1 else 'warning' if avg_js < 0.2 else 'fail',
                        'score': round(max(0, 1 - avg_js), 2),
                        'avg_js_divergence': round(avg_js, 4),
                        'features_passing': f'{passing}/{len(js_scores)}',
                        'target': 'JS < 0.1 for all features'
                    }
        except Exception as e:
            results['pillars']['statistical_fidelity']['error'] = str(e)

        # 2. Causal Fidelity
        try:
            causal = cls.get_causal_mechanism_for_dataset(dataset_id)
            if 'causal_asymmetry' in causal and 'summary' in causal['causal_asymmetry']:
                summary = causal['causal_asymmetry']['summary']
                ut_ratio = summary.get('undertrained_vs_optimal', 0)
                hr_ratio = summary.get('high_risk_vs_optimal', 0)

                is_asymmetric = ut_ratio > hr_ratio and ut_ratio > 1.5

                results['pillars']['causal_fidelity'] = {
                    'status': 'pass' if is_asymmetric else 'warning' if ut_ratio > 1.2 else 'fail',
                    'score': round(min(1.0, ut_ratio / 3.0), 2),
                    'undertrained_risk_ratio': ut_ratio,
                    'high_risk_ratio': hr_ratio,
                    'is_asymmetric': is_asymmetric,
                    'target': 'Undertrained zone shows 2-3x higher risk per load unit',
                    'interpretation': summary.get('interpretation', '')
                }
        except Exception as e:
            results['pillars']['causal_fidelity']['error'] = str(e)

        # 3. Transferability
        try:
            sim2real = cls.run_sim2real_for_dataset(dataset_id)
            auc = sim2real.get('auc', 0.5)

            results['pillars']['transferability'] = {
                'status': 'pass' if auc > 0.60 else 'warning' if auc > 0.55 else 'fail',
                'score': round(max(0, (auc - 0.5) * 2), 2),
                'sim2real_auc': round(auc, 4),
                'target': 'Sim2Real AUC > 0.60',
                'interpretation': sim2real.get('interpretation', '')
            }
        except Exception as e:
            results['pillars']['transferability']['error'] = str(e)

        # Overall assessment
        scores = [
            p.get('score', 0)
            for p in results['pillars'].values()
            if isinstance(p, dict) and 'score' in p
        ]
        results['overall_score'] = round(sum(scores) / len(scores), 2) if scores else 0

        passing = sum(1 for p in results['pillars'].values() if p.get('status') == 'pass')
        results['pillars_passing'] = f'{passing}/3'
        results['ready_for_publication'] = passing == 3

        return results
