import os
import json
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from flask import current_app

from ..utils.file_manager import FileManager


class AnalyticsService:
    """Service for analytics and visualization data."""

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
                profile = profile_row.iloc[0].to_dict()
        except FileNotFoundError:
            pass

        return {
            'athlete_id': athlete_id,
            'profile': profile,
            'dates': athlete_data['date'].tolist(),
            'metrics': {
                col: athlete_data[col].tolist()
                for col in athlete_data.columns
                if col not in ['athlete_id', 'date']
            },
            'injury_days': athlete_data[athlete_data['injury'] == 1]['date'].tolist()
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
        zone_distribution = {zone: count / total for zone, count in zone_counts.items()}

        # Calculate injury rate by zone
        injury_by_zone = df.groupby('acwr_zone')['injury'].agg(['sum', 'count'])
        injury_rates = (injury_by_zone['sum'] / injury_by_zone['count']).to_dict()

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
