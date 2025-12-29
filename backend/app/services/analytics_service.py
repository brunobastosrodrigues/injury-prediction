import os
import json
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import joblib

from flask import current_app

from ..utils.file_manager import FileManager
from .preprocessing_service import PreprocessingService

# SHAP is optional - used for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# Lifestyle profile descriptions for athlete dashboard
LIFESTYLE_DESCRIPTIONS = {
    'Highly Disciplined Athlete': {
        'description': 'This athlete maintains exceptional lifestyle habits with optimal sleep (7.5-9h), excellent nutrition, minimal alcohol, and very low stress levels. Their disciplined approach supports rapid recovery and consistent training adaptations.',
        'risk_implications': 'Lower baseline injury risk due to optimal recovery conditions. Strong HRV patterns and consistent sleep quality provide early warning signals when fatigue accumulates.',
        'strengths': ['Excellent recovery capacity', 'Consistent sleep patterns', 'Strong nutritional foundation'],
        'watch_areas': ['May push through warning signs due to high motivation', 'Training load management still critical']
    },
    'Balanced Competitor': {
        'description': 'This athlete balances training with moderate lifestyle flexibility. Good sleep (6.5-8h), solid nutrition, occasional social drinking, and manageable stress levels characterize this profile.',
        'risk_implications': 'Moderate baseline risk. Recovery capacity is good but may be compromised during high-stress periods or after social events.',
        'strengths': ['Good work-life-training balance', 'Sustainable approach', 'Adequate recovery'],
        'watch_areas': ['Weekend social activities may affect Monday recovery', 'Stress spikes need monitoring']
    },
    'Weekend Socializer': {
        'description': 'This athlete maintains decent training consistency but social activities (moderate-heavy drinking, occasional late nights) impact recovery, especially on weekends. Sleep averages 6-7.5h with variable quality.',
        'risk_implications': 'Elevated injury risk, particularly early in the week following social weekends. Alcohol consumption impairs recovery and increases baseline stress.',
        'strengths': ['Maintains training despite social commitments', 'Good exercise adherence'],
        'watch_areas': ['Monday-Tuesday training should be lighter', 'Hydration often compromised', 'Sleep quality highly variable']
    },
    'Sleep-Deprived Workaholic': {
        'description': 'Chronic sleep deficit (4.5-6.5h) combined with high work stress characterizes this profile. Despite time constraints, this athlete maintains training commitment, though recovery is significantly impaired.',
        'risk_implications': 'HIGH baseline injury risk. Chronic sleep deprivation suppresses HRV, elevates resting HR, and severely limits recovery capacity. Training adaptations are compromised.',
        'strengths': ['Strong dedication to training despite constraints', 'Good nutritional awareness'],
        'watch_areas': ['PRIORITY: Increase sleep duration', 'Reduce training volume during high-stress work periods', 'HRV monitoring critical']
    },
    'Under-Recovered Athlete': {
        'description': 'Poor sleep quality (not just duration) and inadequate recovery protocols characterize this profile. Training is consistent but adaptation is limited by insufficient recovery.',
        'risk_implications': 'HIGH injury risk from accumulated fatigue. Sleep quality issues prevent deep recovery even with adequate sleep duration. Stress sensitivity is elevated.',
        'strengths': ['Good training consistency', 'Moderate exercise adherence'],
        'watch_areas': ['Focus on sleep QUALITY not just quantity', 'Recovery days must be true rest', 'Consider sleep hygiene improvements']
    },
    'Health-Conscious Athlete': {
        'description': 'Strong focus on overall health with good sleep (7-8.5h), excellent nutrition, minimal alcohol, and low stress. Very similar to Highly Disciplined but with slightly less rigid adherence.',
        'risk_implications': 'Low baseline risk. Well-rounded approach to health supports consistent training and good recovery.',
        'strengths': ['Holistic health approach', 'Good stress management', 'Quality nutrition'],
        'watch_areas': ['May benefit from slightly more training stimulus', 'Could optimize sleep for even better recovery']
    }
}


from scipy.spatial.distance import jensenshannon

class AnalyticsService:
    """Service for analytics and visualization data."""

    @classmethod
    def validate_distributions(cls, synthetic_df: pd.DataFrame, real_df: pd.DataFrame, features: List[str] = None) -> Dict[str, Any]:
        """
        Compares synthetic vs real data distributions.
        Returns statistical distance metrics (Jensen-Shannon Divergence).
        """
        if features is None:
            features = ['sleep_quality_daily', 'stress_score']
            
        results = {}
        
        # Mapping for common column discrepancies between schemas
        # Synthetic (standard) -> Real (adapter output)
        col_map = {
            'sleep_quality': 'sleep_quality_daily',
            'stress': 'stress_score',
            'body_battery_morning': 'recovery_score'
        }
        
        for feature in features:
            # Handle column names if they differ
            synth_col = feature
            real_col = col_map.get(feature, feature)
            
            if synth_col not in synthetic_df.columns or real_col not in real_df.columns:
                results[feature] = {'error': 'Column missing in one of the datasets'}
                continue

            # Get data
            synth_data = synthetic_df[synth_col].dropna()
            real_data = real_df[real_col].dropna()
            
            if len(synth_data) == 0 or len(real_data) == 0:
                results[feature] = {'error': 'Empty data'}
                continue
            
            # Calculate histograms for JS Divergence
            # Normalize to form probability distributions
            range_min = min(synth_data.min(), real_data.min())
            range_max = max(synth_data.max(), real_data.max())
            
            # Use fixed number of bins
            try:
                bins = np.linspace(range_min, range_max, 20)
                
                p, _ = np.histogram(synth_data, bins=bins, density=True)
                q, _ = np.histogram(real_data, bins=bins, density=True)
                
                # Add small epsilon to avoid division by zero
                p = p + 1e-10
                q = q + 1e-10
                
                js_dist = jensenshannon(p, q)
                
                results[feature] = {
                    'js_divergence': float(js_dist),
                    'synthetic_mean': float(synth_data.mean()),
                    'real_mean': float(real_data.mean()),
                    'synthetic_std': float(synth_data.std()),
                    'real_std': float(real_data.std()),
                    'status': 'PASS' if js_dist < 0.2 else 'WARNING'
                }
            except Exception as e:
                results[feature] = {'error': str(e)}
        
        return results

    @classmethod
    def simulate_intervention(
        cls,
        model_id: str,
        athlete_id: str,
        date: str,
        overrides: Dict[str, Any]
    ) -> Optional[Dict[str, float]]:
        """
        Simulate an intervention by modifying metrics and recalculating risk.
        """
        # 1. Load Model and Metadata
        models_dir = current_app.config['MODELS_DIR']
        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            return None

        try:
            model = joblib.load(model_path)
        except Exception:
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        dataset_id = metadata.get('dataset_id')
        feature_names = metadata.get('feature_names')

        # 2. Load Raw Data
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            activity_df = FileManager.read_df(os.path.join(dataset_path, 'activity_data'))
        except FileNotFoundError:
            return None

        # Filter for specific athlete to speed up processing
        athlete_daily = daily_df[daily_df['athlete_id'] == athlete_id].copy()
        athlete_activity = activity_df[activity_df['athlete_id'] == athlete_id].copy()
        athlete_profile = athletes_df[athletes_df['athlete_id'] == athlete_id].copy()

        if len(athlete_daily) == 0:
            return None

        # 3. Apply Overrides
        target_date = pd.to_datetime(date)
        athlete_daily['date'] = pd.to_datetime(athlete_daily['date'])
        mask = athlete_daily['date'] == target_date
        
        if not mask.any():
            return None

        # Create a modified copy
        athlete_daily_mod = athlete_daily.copy()
        
        # Handle derived metrics (Training Load)
        if 'duration_minutes' in overrides or 'intensity_factor' in overrides:
            duration = float(overrides.get('duration_minutes', 60))
            intensity = float(overrides.get('intensity_factor', 1.0))
            new_tss = (duration / 60) * (intensity ** 2) * 100
            overrides['actual_tss'] = new_tss

        # Apply overrides to the modified copy
        for key, value in overrides.items():
            if key in athlete_daily_mod.columns:
                athlete_daily_mod.loc[mask, key] = value

        # 4. Run Preprocessing Pipeline
        def process_to_features(d_df, a_df, act_df):
            merged = PreprocessingService._merge_data(a_df, d_df, act_df)
            X = PreprocessingService._engineer_features(merged)
            X_encoded = PreprocessingService._encode_categorical(X)
            return X_encoded, merged

        try:
            X_orig, merged_orig = process_to_features(athlete_daily, athlete_profile, athlete_activity)
            X_mod, merged_mod = process_to_features(athlete_daily_mod, athlete_profile, athlete_activity)
        except Exception:
            return None

        # 5. Extract Feature Vector
        row_idx_orig = merged_orig[merged_orig['date'] == target_date].index
        row_idx_mod = merged_mod[merged_mod['date'] == target_date].index

        if len(row_idx_orig) == 0 or len(row_idx_mod) == 0:
            return None

        def align_features(X, idx):
            row = X.loc[idx].copy()
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            for col in feature_names:
                if col not in row.index:
                    row[col] = 0
            return row[feature_names].to_frame().T

        vector_orig = align_features(X_orig, row_idx_orig)
        vector_mod = align_features(X_mod, row_idx_mod)

        # 6. Predict
        try:
            prob_orig = model.predict_proba(vector_orig)[0][1]
            prob_mod = model.predict_proba(vector_mod)[0][1]
        except Exception:
            return None

        return {
            "original_risk": float(prob_orig),
            "new_risk": float(prob_mod),
            "risk_reduction": float(prob_orig - prob_mod)
        }

    @classmethod
    def get_distribution(cls, dataset_id: str, feature: str, bins: int = 50) -> Optional[Dict[str, Any]]:
        """Get histogram data for a feature distribution."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        if feature not in df.columns:
            return None

        data = df[feature].dropna()
        hist, bin_edges = np.histogram(data, bins=bins)

        return {
            'feature': feature,
            'histogram': hist.tolist(),
            'bin_edges': bin_edges.tolist(),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'median': float(data.median())
        }

    @classmethod
    def get_correlations(cls, dataset_id: str, features: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get correlation matrix for specified features."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        # Default features for correlation
        if features is None:
            features = ['hrv', 'resting_hr', 'sleep_hours', 'sleep_quality',
                       'stress', 'body_battery_morning', 'actual_tss', 'injury']

        # Filter to available features
        available_features = [f for f in features if f in df.columns]
        if len(available_features) < 2:
            return None

        corr_matrix = df[available_features].corr()

        return {
            'features': available_features,
            'correlation_matrix': corr_matrix.values.tolist(),
            'feature_names': corr_matrix.columns.tolist()
        }

    @classmethod
    def get_pre_injury_window(cls, dataset_id: str, lookback_days: int = 14) -> Optional[Dict[str, Any]]:
        """Analyze metrics in the window before injuries."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['athlete_id', 'date'])

        # Find injury onset days
        df['injury_onset'] = 0
        for athlete_id in df['athlete_id'].unique():
            athlete_data = df[df['athlete_id'] == athlete_id]
            for i in range(1, len(athlete_data)):
                curr_idx = athlete_data.index[i]
                prev_idx = athlete_data.index[i-1]
                if df.loc[curr_idx, 'injury'] == 1 and df.loc[prev_idx, 'injury'] == 0:
                    df.loc[curr_idx, 'injury_onset'] = 1

        metrics = ['hrv', 'resting_hr', 'sleep_hours', 'sleep_quality', 'stress', 'body_battery_morning']
        available_metrics = [m for m in metrics if m in df.columns]

        window_analysis = {m: {'days': list(range(-lookback_days, 1)), 'values': []} for m in available_metrics}

        # For each injury onset, collect the preceding days' metrics
        injury_onsets = df[df['injury_onset'] == 1]

        for _, onset in injury_onsets.iterrows():
            athlete_data = df[df['athlete_id'] == onset['athlete_id']].copy()
            athlete_data = athlete_data.sort_values('date')

            onset_idx = athlete_data[athlete_data['date'] == onset['date']].index
            if len(onset_idx) == 0:
                continue

            onset_pos = athlete_data.index.get_loc(onset_idx[0])

            for m in available_metrics:
                values = []
                for day in range(-lookback_days, 1):
                    pos = onset_pos + day
                    if 0 <= pos < len(athlete_data):
                        values.append(float(athlete_data.iloc[pos][m]))
                    else:
                        values.append(None)
                window_analysis[m]['values'].append(values)

        # Calculate averages
        result = {}
        for m in available_metrics:
            all_values = window_analysis[m]['values']
            if all_values:
                avg_values = []
                for day_idx in range(lookback_days + 1):
                    day_values = [v[day_idx] for v in all_values if v[day_idx] is not None]
                    avg_values.append(float(np.mean(day_values)) if day_values else None)
                result[m] = {
                    'days': list(range(-lookback_days, 1)),
                    'average': avg_values,
                    'n_samples': len(all_values)
                }

        return {
            'lookback_days': lookback_days,
            'n_injuries': len(injury_onsets),
            'metrics': result
        }

    @classmethod
    def get_athlete_timeline(cls, dataset_id: str, athlete_id: str) -> Optional[Dict[str, Any]]:
        """Get time series data for a specific athlete."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        athlete_data = daily_df[daily_df['athlete_id'] == athlete_id].copy()

        if len(athlete_data) == 0:
            return None

        athlete_data = athlete_data.sort_values('date')

        # Get athlete profile
        profile = None
        try:
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            profile_row = athletes_df[athletes_df['athlete_id'] == athlete_id]
            if len(profile_row) > 0:
                # Convert numpy types to python types for serialization
                profile = json.loads(profile_row.iloc[0].to_json())
        except FileNotFoundError:
            pass

        return {
            'athlete_id': athlete_id,
            'profile': profile,
            'dates': athlete_data['date'].dt.strftime('%Y-%m-%d').tolist(),
            'metrics': {
                col: athlete_data[col].tolist()
                for col in athlete_data.columns
                if col not in ['athlete_id', 'date']
            },
            'injury_days': athlete_data[athlete_data['injury'] == 1]['date'].dt.strftime('%Y-%m-%d').tolist()
        }

    @classmethod
    def get_acwr_zones(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Analyze ACWR zone distribution and injury rates."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        df = df.sort_values(['athlete_id', 'date'])

        # Calculate ACWR
        def calc_acwr(group):
            group = group.copy()
            group['acute_load'] = group['actual_tss'].rolling(7, min_periods=1).sum()
            group['chronic_load'] = group['actual_tss'].rolling(28, min_periods=7).mean() * 7
            group['acwr'] = group['acute_load'] / group['chronic_load'].replace(0, np.nan)
            return group

        df = df.groupby('athlete_id', group_keys=False).apply(calc_acwr)
        df['acwr'] = df['acwr'].fillna(1.0)

        # Define zones
        def acwr_zone(acwr):
            if acwr < 0.8:
                return 'Too Low (<0.8)'
            elif acwr < 1.3:
                return 'Optimal (0.8-1.3)'
            elif acwr < 1.5:
                return 'Danger Zone (1.3-1.5)'
            else:
                return 'High Risk (>1.5)'

        df['acwr_zone'] = df['acwr'].apply(acwr_zone)

        # Calculate zone distribution
        zone_counts = df['acwr_zone'].value_counts().to_dict()
        total = len(df)
        # Prevent division by zero when dataset is empty
        zone_distribution = {zone: count / total if total > 0 else 0 for zone, count in zone_counts.items()}

        # Calculate injury rate by zone
        injury_by_zone = df.groupby('acwr_zone')['injury'].agg(['sum', 'count'])
        # Prevent division by zero with replace
        injury_rates = (injury_by_zone['sum'] / injury_by_zone['count'].replace(0, 1)).to_dict()

        return {
            'zone_distribution': zone_distribution,
            'injury_rate_by_zone': injury_rates,
            'total_days': total,
            'zone_order': ['Too Low (<0.8)', 'Optimal (0.8-1.3)', 'Danger Zone (1.3-1.5)', 'High Risk (>1.5)']
        }

    @classmethod
    def get_feature_importance(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get feature importance from a trained model."""
        models_dir = current_app.config['MODELS_DIR']
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if not os.path.exists(metadata_path):
            return None

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return {
            'model_id': model_id,
            'model_type': metadata.get('model_type'),
            'feature_importance': metadata.get('feature_importance', [])
        }

    @classmethod
    def list_athletes(cls, dataset_id: str) -> Optional[List[str]]:
        """List all athlete IDs in a dataset."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            return df['athlete_id'].tolist()
        except FileNotFoundError:
            return None

    @classmethod
    def get_dataset_stats(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get overall statistics for a dataset."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        stats = {
            'n_athletes': daily_df['athlete_id'].nunique(),
            'n_days': len(daily_df),
            'injury_rate': float(daily_df['injury'].mean()),
            'total_injuries': int(daily_df['injury'].sum())
        }

        # Add per-metric stats
        numeric_cols = daily_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['athlete_id', 'injury']:
                stats[f'{col}_mean'] = float(daily_df[col].mean())
                stats[f'{col}_std'] = float(daily_df[col].std())

        try:
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            if 'gender' in athletes_df.columns:
                stats['gender_distribution'] = athletes_df['gender'].value_counts().to_dict()
            if 'age' in athletes_df.columns:
                stats['age_mean'] = float(athletes_df['age'].mean())
                stats['age_std'] = float(athletes_df['age'].std())
        except FileNotFoundError:
            pass

        return stats

    # ============================================
    # NEW ATHLETE DASHBOARD METHODS
    # ============================================

    @classmethod
    def get_athlete_profile_detailed(cls, dataset_id: str, athlete_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed athlete profile with lifestyle context and summary stats."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        except FileNotFoundError:
            return None

        # Get athlete profile
        athlete_row = athletes_df[athletes_df['athlete_id'] == athlete_id]
        if len(athlete_row) == 0:
            return None

        profile = json.loads(athlete_row.iloc[0].to_json())

        # Get athlete's daily data for summary stats
        athlete_daily = daily_df[daily_df['athlete_id'] == athlete_id]
        if len(athlete_daily) == 0:
            return None

        # Calculate summary statistics
        summary_stats = {
            'total_days': len(athlete_daily),
            'total_injuries': int(athlete_daily['injury'].sum()),
            'injury_rate': float(athlete_daily['injury'].mean()),
            'avg_hrv': float(athlete_daily['hrv'].mean()) if 'hrv' in athlete_daily.columns else None,
            'avg_resting_hr': float(athlete_daily['resting_hr'].mean()) if 'resting_hr' in athlete_daily.columns else None,
            'avg_sleep_hours': float(athlete_daily['sleep_hours'].mean()) if 'sleep_hours' in athlete_daily.columns else None,
            'avg_sleep_quality': float(athlete_daily['sleep_quality'].mean()) if 'sleep_quality' in athlete_daily.columns else None,
            'avg_stress': float(athlete_daily['stress'].mean()) if 'stress' in athlete_daily.columns else None,
            'avg_tss': float(athlete_daily['actual_tss'].mean()) if 'actual_tss' in athlete_daily.columns else None,
            'avg_body_battery_morning': float(athlete_daily['body_battery_morning'].mean()) if 'body_battery_morning' in athlete_daily.columns else None,
        }

        # Get lifestyle profile description
        lifestyle_name = profile.get('lifestyle', 'Unknown')
        lifestyle_info = LIFESTYLE_DESCRIPTIONS.get(lifestyle_name, {
            'description': 'No detailed profile information available.',
            'risk_implications': 'Standard monitoring recommended.',
            'strengths': [],
            'watch_areas': []
        })

        # Extract lifestyle factors
        lifestyle_factors = {
            'sleep_time_norm': profile.get('sleep_time_norm'),
            'sleep_quality': profile.get('sleep_quality'),
            'nutrition_factor': profile.get('nutrition_factor'),
            'stress_factor': profile.get('stress_factor'),
            'smoking_factor': profile.get('smoking_factor'),
            'drinking_factor': profile.get('drinking_factor'),
        }

        return {
            'athlete_id': athlete_id,
            'profile': profile,
            'lifestyle_factors': lifestyle_factors,
            'lifestyle_info': lifestyle_info,
            'summary_stats': summary_stats
        }

    @classmethod
    def get_athlete_pre_injury_patterns(
        cls,
        dataset_id: str,
        athlete_id: str,
        lookback_days: int = 14
    ) -> Optional[Dict[str, Any]]:
        """Analyze this specific athlete's pre-injury patterns."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
        except FileNotFoundError:
            return None

        # Filter for this athlete
        athlete_daily = daily_df[daily_df['athlete_id'] == athlete_id].copy()
        if len(athlete_daily) == 0:
            return None

        athlete_daily['date'] = pd.to_datetime(athlete_daily['date'])
        athlete_daily = athlete_daily.sort_values('date').reset_index(drop=True)

        # Get athlete's baseline HRV for normalization
        athlete_profile = athletes_df[athletes_df['athlete_id'] == athlete_id]
        hrv_baseline = float(athlete_profile['hrv_baseline'].iloc[0]) if len(athlete_profile) > 0 and 'hrv_baseline' in athlete_profile.columns else None

        # Find injury onset days (transition from non-injury to injury)
        athlete_daily['injury_onset'] = (
            (athlete_daily['injury'] == 1) &
            (athlete_daily['injury'].shift(1) == 0)
        ).astype(int)

        injury_onsets = athlete_daily[athlete_daily['injury_onset'] == 1]
        n_injuries = len(injury_onsets)

        if n_injuries == 0:
            return {
                'athlete_id': athlete_id,
                'n_injuries': 0,
                'patterns': {},
                'pattern_summary': {
                    'primary_indicator': None,
                    'secondary_indicators': [],
                    'typical_warning_window': None,
                    'message': 'No injuries recorded for this athlete.'
                }
            }

        # Metrics to analyze
        metrics = ['hrv', 'resting_hr', 'sleep_quality', 'stress', 'body_battery_morning', 'sleep_hours']
        available_metrics = [m for m in metrics if m in athlete_daily.columns]

        patterns = {}
        for metric in available_metrics:
            patterns[metric] = {
                'days': list(range(-lookback_days, 1)),
                'values_by_injury': [],
                'average': [],
                'baseline_avg': float(athlete_daily[metric].mean()),
            }

        # Collect pre-injury windows for each injury
        for _, onset in injury_onsets.iterrows():
            onset_idx = athlete_daily[athlete_daily['date'] == onset['date']].index[0]

            for metric in available_metrics:
                values = []
                for day_offset in range(-lookback_days, 1):
                    idx = onset_idx + day_offset
                    if 0 <= idx < len(athlete_daily):
                        values.append(float(athlete_daily.iloc[idx][metric]))
                    else:
                        values.append(None)
                patterns[metric]['values_by_injury'].append(values)

        # Calculate averages and changes
        metric_changes = {}
        for metric in available_metrics:
            all_values = patterns[metric]['values_by_injury']
            if all_values:
                avg_values = []
                for day_idx in range(lookback_days + 1):
                    day_values = [v[day_idx] for v in all_values if v[day_idx] is not None]
                    avg_values.append(float(np.mean(day_values)) if day_values else None)
                patterns[metric]['average'] = avg_values

                # Calculate change from baseline (day -14) to injury (day 0)
                if avg_values[0] is not None and avg_values[-1] is not None and avg_values[0] != 0:
                    pct_change = ((avg_values[-1] - avg_values[0]) / abs(avg_values[0])) * 100
                    patterns[metric]['change_percentage'] = round(pct_change, 1)
                    metric_changes[metric] = abs(pct_change)
                else:
                    patterns[metric]['change_percentage'] = None

        # Determine primary and secondary indicators
        sorted_changes = sorted(metric_changes.items(), key=lambda x: x[1], reverse=True)
        primary_indicator = sorted_changes[0][0] if sorted_changes else None
        secondary_indicators = [m[0] for m in sorted_changes[1:3]] if len(sorted_changes) > 1 else []

        # Estimate warning window (when metrics start deviating significantly)
        warning_window = lookback_days
        if primary_indicator and patterns[primary_indicator]['average']:
            avg = patterns[primary_indicator]['average']
            baseline = avg[0] if avg[0] else patterns[primary_indicator]['baseline_avg']
            if baseline:
                for i, val in enumerate(avg):
                    if val and abs(val - baseline) / abs(baseline) > 0.05:  # 5% deviation
                        warning_window = lookback_days - i
                        break

        return {
            'athlete_id': athlete_id,
            'n_injuries': n_injuries,
            'hrv_baseline': hrv_baseline,
            'patterns': patterns,
            'pattern_summary': {
                'primary_indicator': primary_indicator,
                'secondary_indicators': secondary_indicators,
                'typical_warning_window': warning_window,
                'message': f'Your injuries are typically preceded by changes in {primary_indicator} starting approximately {warning_window} days before.' if primary_indicator else None
            }
        }

    @classmethod
    def get_athlete_risk_timeline(
        cls,
        dataset_id: str,
        athlete_id: str,
        model_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate continuous risk predictions over athlete's timeline."""
        models_dir = current_app.config['MODELS_DIR']
        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            return None

        try:
            model = joblib.load(model_path)
        except Exception:
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        feature_names = metadata.get('feature_names', [])

        # Load raw data
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            activity_df = FileManager.read_df(os.path.join(dataset_path, 'activity_data'))
        except FileNotFoundError:
            return None

        # Filter for athlete
        athlete_daily = daily_df[daily_df['athlete_id'] == athlete_id].copy()
        athlete_activity = activity_df[activity_df['athlete_id'] == athlete_id].copy()
        athlete_profile = athletes_df[athletes_df['athlete_id'] == athlete_id].copy()

        if len(athlete_daily) == 0:
            return None

        athlete_daily['date'] = pd.to_datetime(athlete_daily['date'])
        athlete_daily = athlete_daily.sort_values('date')

        # Run preprocessing to get features
        try:
            merged = PreprocessingService._merge_data(athlete_profile, athlete_daily, athlete_activity)
            X = PreprocessingService._engineer_features(merged)
            X_encoded = PreprocessingService._encode_categorical(X)
        except Exception:
            return None

        # Align features with model
        for col in feature_names:
            if col not in X_encoded.columns:
                X_encoded[col] = 0
        X_aligned = X_encoded[feature_names]

        # Predict risk for each day
        try:
            risk_scores = model.predict_proba(X_aligned)[:, 1].tolist()
        except Exception:
            return None

        # Get injury days
        injury_days = athlete_daily[athlete_daily['injury'] == 1]['date'].dt.strftime('%Y-%m-%d').tolist()

        return {
            'athlete_id': athlete_id,
            'model_id': model_id,
            'dates': athlete_daily['date'].dt.strftime('%Y-%m-%d').tolist(),
            'risk_scores': risk_scores,
            'injury_days': injury_days,
            'risk_thresholds': {
                'low': 0.05,
                'moderate': 0.15,
                'high': 0.30
            },
            'avg_risk': float(np.mean(risk_scores)),
            'max_risk': float(np.max(risk_scores)),
            'days_above_moderate': int(sum(1 for r in risk_scores if r > 0.15))
        }

    @classmethod
    def get_athlete_risk_factors(
        cls,
        dataset_id: str,
        athlete_id: str,
        model_id: str,
        date: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get SHAP or feature importance breakdown for this athlete."""
        models_dir = current_app.config['MODELS_DIR']
        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            return None

        try:
            model = joblib.load(model_path)
        except Exception:
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        feature_names = metadata.get('feature_names', [])
        model_type = metadata.get('model_type', 'unknown')

        # Load raw data
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)

        try:
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            activity_df = FileManager.read_df(os.path.join(dataset_path, 'activity_data'))
        except FileNotFoundError:
            return None

        # Filter for athlete
        athlete_daily = daily_df[daily_df['athlete_id'] == athlete_id].copy()
        athlete_activity = activity_df[activity_df['athlete_id'] == athlete_id].copy()
        athlete_profile = athletes_df[athletes_df['athlete_id'] == athlete_id].copy()

        if len(athlete_daily) == 0:
            return None

        athlete_daily['date'] = pd.to_datetime(athlete_daily['date'])
        athlete_daily = athlete_daily.sort_values('date')

        # If no date specified, use the latest
        if date is None:
            target_date = athlete_daily['date'].max()
        else:
            target_date = pd.to_datetime(date)

        # Run preprocessing
        try:
            merged = PreprocessingService._merge_data(athlete_profile, athlete_daily, athlete_activity)
            X = PreprocessingService._engineer_features(merged)
            X_encoded = PreprocessingService._encode_categorical(X)
        except Exception:
            return None

        # Align features
        for col in feature_names:
            if col not in X_encoded.columns:
                X_encoded[col] = 0
        X_aligned = X_encoded[feature_names]

        # Get row for target date
        merged['date'] = pd.to_datetime(merged['date'])
        row_mask = merged['date'] == target_date
        if not row_mask.any():
            return None

        row_idx = merged[row_mask].index[0]
        if row_idx not in X_aligned.index:
            return None

        X_sample = X_aligned.loc[[row_idx]]

        # Get current risk
        try:
            current_risk = float(model.predict_proba(X_sample)[0][1])
        except Exception:
            return None

        # Calculate feature contributions
        contributions = []

        if SHAP_AVAILABLE and model_type in ['random_forest', 'xgboost']:
            try:
                # Use SHAP for tree-based models
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_sample)

                # Handle binary classification
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # Positive class

                shap_values = shap_values[0]  # First (only) sample

                for i, feature in enumerate(feature_names):
                    contributions.append({
                        'feature': feature,
                        'contribution': float(shap_values[i]),
                        'value': float(X_sample[feature].iloc[0]),
                        'direction': 'positive' if shap_values[i] > 0 else 'negative'
                    })
            except Exception:
                # Fallback to feature importance
                contributions = cls._get_feature_importance_contributions(
                    model, feature_names, X_sample, metadata
                )
        else:
            # Use feature importance approximation for other models
            contributions = cls._get_feature_importance_contributions(
                model, feature_names, X_sample, metadata
            )

        # Sort by absolute contribution
        contributions = sorted(contributions, key=lambda x: abs(x['contribution']), reverse=True)

        # Group by lifestyle category
        lifestyle_categories = {
            'sleep': ['sleep_hours', 'sleep_quality', 'deep_sleep', 'rem_sleep', 'light_sleep', 'poor_sleep'],
            'stress': ['stress', 'stress_7d_avg', 'stress_volatility'],
            'recovery': ['hrv', 'hrv_ratio', 'resting_hr', 'rhr_ratio', 'body_battery_morning', 'body_battery_evening', 'body_battery_drain'],
            'training': ['actual_tss', 'tss_7d_avg', 'tss_28d_avg', 'acwr', 'form', 'ctl', 'atl', 'consecutive_high_load_days']
        }

        lifestyle_impact = {}
        for category, features in lifestyle_categories.items():
            category_contributions = [c for c in contributions if any(f in c['feature'].lower() for f in features)]
            if category_contributions:
                total_contribution = sum(c['contribution'] for c in category_contributions)
                lifestyle_impact[category] = {
                    'contribution': float(total_contribution),
                    'assessment': 'elevated' if total_contribution > 0.02 else 'below_optimal' if total_contribution < -0.02 else 'optimal',
                    'top_factors': [c['feature'] for c in category_contributions[:2]]
                }

        return {
            'athlete_id': athlete_id,
            'date': target_date.strftime('%Y-%m-%d'),
            'current_risk': current_risk,
            'factor_contributions': contributions[:15],  # Top 15
            'lifestyle_impact': lifestyle_impact,
            'model_type': model_type
        }

    @classmethod
    def _get_feature_importance_contributions(
        cls,
        model,
        feature_names: List[str],
        X_sample: pd.DataFrame,
        metadata: Dict
    ) -> List[Dict]:
        """Fallback method to estimate contributions using feature importance."""
        contributions = []

        # Try to get feature importance from model
        feature_importance = metadata.get('feature_importance', [])
        importance_dict = {item['feature']: item['importance'] for item in feature_importance}

        for feature in feature_names:
            importance = importance_dict.get(feature, 0)
            value = float(X_sample[feature].iloc[0]) if feature in X_sample.columns else 0

            # Approximate contribution as importance * normalized value
            # This is a rough approximation
            contribution = importance * (value / 100 if value > 1 else value)

            contributions.append({
                'feature': feature,
                'contribution': float(contribution),
                'value': value,
                'direction': 'positive' if contribution > 0 else 'negative'
            })

        return contributions

    @classmethod
    def get_athlete_recommendations(
        cls,
        dataset_id: str,
        athlete_id: str,
        model_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate personalized recommendations based on current metrics."""
        # Get athlete profile and current status
        profile_data = cls.get_athlete_profile_detailed(dataset_id, athlete_id)
        if not profile_data:
            return None

        # Get current timeline data
        timeline_data = cls.get_athlete_timeline(dataset_id, athlete_id)
        if not timeline_data:
            return None

        # Get current risk
        risk_timeline = cls.get_athlete_risk_timeline(dataset_id, athlete_id, model_id)
        current_risk = risk_timeline['risk_scores'][-1] if risk_timeline and risk_timeline['risk_scores'] else 0.1

        # Get latest metrics
        metrics = timeline_data['metrics']
        latest_idx = -1

        current_metrics = {
            'sleep_hours': metrics.get('sleep_hours', [7])[latest_idx] if metrics.get('sleep_hours') else 7,
            'sleep_quality': metrics.get('sleep_quality', [0.7])[latest_idx] if metrics.get('sleep_quality') else 0.7,
            'stress': metrics.get('stress', [50])[latest_idx] if metrics.get('stress') else 50,
            'hrv': metrics.get('hrv', [60])[latest_idx] if metrics.get('hrv') else 60,
            'actual_tss': metrics.get('actual_tss', [80])[latest_idx] if metrics.get('actual_tss') else 80,
        }

        # Get athlete baselines
        profile = profile_data['profile']
        baselines = {
            'sleep_hours': profile.get('sleep_time_norm', 7.5),
            'sleep_quality': profile.get('sleep_quality', 0.8),
            'hrv': profile.get('hrv_baseline', 70),
        }

        recommendations = []

        # Sleep recommendations
        sleep_deficit = baselines['sleep_hours'] - current_metrics['sleep_hours']
        if sleep_deficit > 0.5:
            # Simulate intervention
            sim_result = cls.simulate_intervention(
                model_id, athlete_id, timeline_data['dates'][-1],
                {'sleep_hours': baselines['sleep_hours']}
            )
            risk_reduction = sim_result['risk_reduction'] if sim_result else 0

            recommendations.append({
                'category': 'sleep',
                'priority': 'high' if sleep_deficit > 1.5 else 'medium',
                'title': f'Increase sleep to {baselines["sleep_hours"]:.1f}+ hours',
                'description': f'Your current sleep ({current_metrics["sleep_hours"]:.1f}h) is {sleep_deficit:.1f}h below your optimal baseline. Adequate sleep is critical for recovery and injury prevention.',
                'expected_risk_reduction': risk_reduction,
                'current_value': current_metrics['sleep_hours'],
                'optimal_range': [baselines['sleep_hours'] - 0.5, baselines['sleep_hours'] + 1]
            })

        # Stress recommendations
        if current_metrics['stress'] > 60:
            sim_result = cls.simulate_intervention(
                model_id, athlete_id, timeline_data['dates'][-1],
                {'stress': 40}
            )
            risk_reduction = sim_result['risk_reduction'] if sim_result else 0

            recommendations.append({
                'category': 'stress',
                'priority': 'high' if current_metrics['stress'] > 75 else 'medium',
                'title': 'Reduce stress levels',
                'description': f'Your stress level ({current_metrics["stress"]:.0f}) is elevated. Consider stress management techniques, lighter training, or rest days.',
                'expected_risk_reduction': risk_reduction,
                'current_value': current_metrics['stress'],
                'optimal_range': [20, 50]
            })

        # HRV recommendations
        hrv_ratio = current_metrics['hrv'] / baselines['hrv'] if baselines['hrv'] > 0 else 1
        if hrv_ratio < 0.85:
            recommendations.append({
                'category': 'recovery',
                'priority': 'high' if hrv_ratio < 0.75 else 'medium',
                'title': 'Recovery day recommended',
                'description': f'Your HRV ({current_metrics["hrv"]:.0f}ms) is {(1-hrv_ratio)*100:.0f}% below your baseline ({baselines["hrv"]:.0f}ms). This indicates accumulated fatigue - consider a rest or light recovery day.',
                'expected_risk_reduction': 0.02,  # Estimate
                'current_value': current_metrics['hrv'],
                'optimal_range': [baselines['hrv'] * 0.9, baselines['hrv'] * 1.1]
            })

        # Training load recommendations
        if current_metrics['actual_tss'] > 150:
            sim_result = cls.simulate_intervention(
                model_id, athlete_id, timeline_data['dates'][-1],
                {'duration_minutes': 60, 'intensity_factor': 0.7}
            )
            risk_reduction = sim_result['risk_reduction'] if sim_result else 0

            recommendations.append({
                'category': 'training',
                'priority': 'medium',
                'title': 'Moderate training load today',
                'description': f'Your recent TSS ({current_metrics["actual_tss"]:.0f}) is high. Consider a lighter session to allow recovery.',
                'expected_risk_reduction': risk_reduction,
                'current_value': current_metrics['actual_tss'],
                'optimal_range': [50, 120]
            })

        # Sort by priority and expected risk reduction
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 2), -x['expected_risk_reduction']))

        # Get lifestyle context
        lifestyle_info = profile_data.get('lifestyle_info', {})

        return {
            'athlete_id': athlete_id,
            'current_risk': current_risk,
            'recommendations': recommendations,
            'lifestyle_context': {
                'profile': profile.get('lifestyle', 'Unknown'),
                'description': lifestyle_info.get('description', ''),
                'key_risk_areas': lifestyle_info.get('watch_areas', []),
                'strengths': lifestyle_info.get('strengths', [])
            },
            'current_metrics': current_metrics,
            'baselines': baselines
        }
