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
        # Try multiple paths
        possible_paths = [
            os.path.join(current_app.config.get('BASE_DIR', os.getcwd()), 'data', 'external', 'pmdata'),
            os.path.join(os.path.dirname(current_app.root_path), 'data', 'external', 'pmdata'),
            '/home/rodrigues/injury-prediction/backend/data/external/pmdata',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]

    @classmethod
    def get_synthetic_path(cls) -> Optional[str]:
        """Get the latest synthetic dataset path."""
        from flask import current_app
        # Try multiple paths
        possible_paths = [
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
                    spearman_r, spearman_p = stats.spearmanr(df[feat], df[target])
                    correlations.append({
                        'feature': feat,
                        'correlation': round(float(spearman_r), 4),
                        'p_value': round(float(spearman_p), 4),
                        'significant': spearman_p < 0.05,
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
