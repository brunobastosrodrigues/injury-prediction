import os
import sys
import uuid
import json
import threading
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import ast

from flask import current_app
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupShuffleSplit

from ..utils.progress_tracker import ProgressTracker
from ..utils.file_manager import FileManager


class PreprocessingService:
    """Service for preprocessing and feature engineering."""

    @classmethod
    def preprocess_async(
        cls,
        dataset_id: str,
        split_strategy: str = 'athlete_based',
        split_ratio: float = 0.2,
        prediction_window: int = 7,
        random_seed: int = 42
    ) -> str:
        """Start async preprocessing and return job_id."""
        job_id = ProgressTracker.create_job('preprocessing')

        thread = threading.Thread(
            target=cls._run_preprocessing,
            args=(job_id, dataset_id, split_strategy, split_ratio, prediction_window, random_seed),
            daemon=True
        )
        thread.start()

        return job_id

    @classmethod
    def _run_preprocessing(
        cls,
        job_id: str,
        dataset_id: str,
        split_strategy: str,
        split_ratio: float,
        prediction_window: int,
        random_seed: int
    ):
        """Run the actual preprocessing (in background thread)."""
        try:
            from app import create_app
            app = create_app()

            with app.app_context():
                ProgressTracker.start_job(job_id, total_steps=6)

                # Step 1: Load data
                ProgressTracker.update_progress(job_id, 10, 'Loading data...')
                raw_dir = current_app.config['RAW_DATA_DIR']
                dataset_path = os.path.join(raw_dir, dataset_id)

                athletes_df = pd.read_csv(os.path.join(dataset_path, 'athletes.csv'))
                daily_df = pd.read_csv(os.path.join(dataset_path, 'daily_data.csv'))
                activity_df = pd.read_csv(os.path.join(dataset_path, 'activity_data.csv'))

                # Step 2: Merge data
                ProgressTracker.update_progress(job_id, 20, 'Merging data...')
                merged = cls._merge_data(athletes_df, daily_df, activity_df)

                # Step 3: Engineer injury labels
                ProgressTracker.update_progress(job_id, 35, 'Engineering injury labels...')
                labeled_df = cls._engineer_injury_labels(merged, prediction_window)
                targets_df = cls._create_prediction_targets(labeled_df, prediction_window)

                # Step 4: Feature engineering
                ProgressTracker.update_progress(job_id, 50, 'Engineering features...')
                X = targets_df.drop(['injury', 'injury_onset', 'recovery_day', 'pre_injury',
                                     'injury_state', 'will_get_injured', 'time_to_injury'], axis=1, errors='ignore')
                y = targets_df['will_get_injured']

                X_engineered = cls._engineer_features(X)

                # Step 5: Encode categorical
                ProgressTracker.update_progress(job_id, 70, 'Encoding features...')
                X_encoded = cls._encode_categorical(X_engineered)

                # Step 6: Split data
                ProgressTracker.update_progress(job_id, 85, 'Splitting data...')
                split_id = f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"

                cls._save_split(
                    split_id, X_encoded, y, merged,
                    split_strategy, split_ratio, random_seed,
                    dataset_id, prediction_window
                )

                ProgressTracker.complete_job(job_id, result={'split_id': split_id})

        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")

    @classmethod
    def _merge_data(cls, athletes_df, daily_df, activity_df):
        """Merge athlete, daily, and activity data."""
        # Pivot activity data by sport
        activity_pivot = activity_df.pivot_table(
            index=['athlete_id', 'date'],
            columns='sport',
            values=['duration_minutes', 'tss', 'avg_hr', 'max_hr', 'avg_power',
                    'normalized_power', 'distance_km', 'avg_speed_kph'],
            aggfunc='first'
        ).reset_index()

        # Flatten column names
        activity_pivot.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col
                                   for col in activity_pivot.columns]

        # Merge daily with athletes
        merged = daily_df.merge(athletes_df, on='athlete_id', suffixes=('_daily', '_norm'))

        # Merge with activity (if available)
        if len(activity_pivot) > 0:
            merged = merged.merge(activity_pivot, on=['athlete_id', 'date'], how='left')

        merged['date'] = pd.to_datetime(merged['date'])
        merged.fillna(0, inplace=True)

        return merged

    @classmethod
    def _engineer_injury_labels(cls, df, prediction_window=7):
        """Transform raw injury labels into meaningful labels."""
        result_df = df.copy()
        result_df = result_df.sort_values(['athlete_id', 'date'])

        result_df['injury_onset'] = 0
        result_df['recovery_day'] = 0
        result_df['pre_injury'] = 0
        result_df['injury_state'] = 0

        for athlete_id in result_df['athlete_id'].unique():
            athlete_data = result_df[result_df['athlete_id'] == athlete_id].copy()
            athlete_indices = athlete_data.index

            injury_indices = []
            for i in range(1, len(athlete_indices)):
                prev_idx = athlete_indices[i-1]
                curr_idx = athlete_indices[i]
                if (result_df.loc[curr_idx, 'injury'] == 1 and
                    result_df.loc[prev_idx, 'injury'] == 0):
                    injury_indices.append(curr_idx)

            if len(athlete_indices) > 0 and result_df.loc[athlete_indices[0], 'injury'] == 1:
                injury_indices.append(athlete_indices[0])

            result_df.loc[injury_indices, 'injury_onset'] = 1

            for onset_idx in injury_indices:
                onset_position = list(athlete_indices).index(onset_idx)
                for i in range(1, prediction_window + 1):
                    if onset_position - i >= 0:
                        pre_injury_idx = athlete_indices[onset_position - i]
                        if result_df.loc[pre_injury_idx, 'injury'] == 0:
                            result_df.loc[pre_injury_idx, 'pre_injury'] = 1

            recovery_indices = [idx for idx in athlete_indices
                               if result_df.loc[idx, 'injury'] == 1
                               and idx not in injury_indices]
            result_df.loc[recovery_indices, 'recovery_day'] = 1

            result_df.loc[result_df['injury_onset'] == 1, 'injury_state'] = 2
            result_df.loc[(result_df['recovery_day'] == 1) & (result_df['injury_state'] == 0), 'injury_state'] = 3
            result_df.loc[(result_df['pre_injury'] == 1) & (result_df['injury_state'] == 0), 'injury_state'] = 1

        return result_df

    @classmethod
    def _create_prediction_targets(cls, df, predict_window=7):
        """Create binary target for injury prediction."""
        result_df = df.copy()
        result_df['will_get_injured'] = 0
        result_df['time_to_injury'] = 29  # Max days

        for athlete_id in result_df['athlete_id'].unique():
            athlete_mask = result_df['athlete_id'] == athlete_id
            athlete_data = result_df[athlete_mask].copy()

            for i in range(len(athlete_data) - 1):
                look_ahead = min(predict_window, len(athlete_data) - i - 1)
                if athlete_data['injury_onset'].iloc[i+1:i+1+look_ahead].sum() > 0:
                    result_df.loc[athlete_data.index[i], 'will_get_injured'] = 1

        return result_df

    @classmethod
    def _engineer_features(cls, X):
        """Create features for injury prediction."""
        def safe_ratio(numerator, denominator, default=0, lower_clip=None):
            result = np.where(denominator != 0, numerator / denominator, default)
            result = pd.Series(result).replace([np.inf, -np.inf], default)
            if lower_clip is not None:
                result = result.clip(lower=lower_clip)
            return result

        def rolling_by_athlete(df, column, window, function, min_periods=1):
            return df.groupby('athlete_id')[column].transform(
                lambda x: x.rolling(window=window, min_periods=min_periods).apply(function, raw=True)
            )

        # HRV features
        if 'hrv' in X.columns and 'hrv_baseline' in X.columns:
            X['hrv_ratio'] = X['hrv'] / X['hrv_baseline'].replace(0, 1)
            X['low_hrv_risk'] = (X['hrv_ratio'] < 0.85).astype(int)
            X['hrv_volatility'] = rolling_by_athlete(X, 'hrv', 7, np.std, min_periods=3)

        # Resting HR features
        if 'resting_hr' in X.columns:
            rhr_col = 'resting_hr_daily' if 'resting_hr_daily' in X.columns else 'resting_hr'
            rhr_norm_col = 'resting_hr_norm' if 'resting_hr_norm' in X.columns else 'resting_hr'
            if rhr_norm_col in X.columns:
                X['resting_hr_ratio'] = X[rhr_col] / X[rhr_norm_col].replace(0, 1)

        # Sleep features
        if 'sleep_quality' in X.columns:
            sq_col = 'sleep_quality_daily' if 'sleep_quality_daily' in X.columns else 'sleep_quality'
            X['poor_sleep'] = (X[sq_col] < 0.6).astype(int)

        # Training load features
        if 'actual_tss' in X.columns and 'planned_tss' in X.columns:
            X['tss_deviation'] = X['actual_tss'] - X['planned_tss']
            X['high_tss_day'] = (X['actual_tss'] > X['actual_tss'].quantile(0.85)).astype(int)

        # ACWR features
        if 'actual_tss' in X.columns:
            X['tss_7d_avg'] = rolling_by_athlete(X, 'actual_tss', 7, np.mean)
            X['acute_load'] = rolling_by_athlete(X, 'actual_tss', 7, np.sum)
            X['chronic_load'] = rolling_by_athlete(X, 'actual_tss', 28, np.mean) * 7
            X['acwr'] = safe_ratio(X['acute_load'], X['chronic_load'])

        # Stress features
        if 'stress' in X.columns:
            X['stress_7d_avg'] = rolling_by_athlete(X, 'stress', 7, np.mean)
            X['stress_volatility'] = rolling_by_athlete(X, 'stress', 7, np.std, min_periods=3)

        # Body battery features
        if 'body_battery_morning' in X.columns and 'body_battery_evening' in X.columns:
            X['body_battery_drain'] = X['body_battery_morning'] - X['body_battery_evening']

        return X

    @classmethod
    def _encode_categorical(cls, X):
        """Encode categorical features."""
        # Drop non-numeric columns that can't be used
        columns_to_drop = []
        for col in X.columns:
            if X[col].dtype == 'object':
                try:
                    X[col] = pd.to_numeric(X[col], errors='coerce')
                except:
                    columns_to_drop.append(col)

        if 'athlete_id' in X.columns:
            columns_to_drop.append('athlete_id')

        # Handle date columns
        date_cols = [col for col in X.columns if 'date' in col.lower()]
        for col in date_cols:
            try:
                dt_col = pd.to_datetime(X[col])
                X[f'{col}_dayofweek'] = dt_col.dt.dayofweek
                X[f'{col}_month'] = dt_col.dt.month
                columns_to_drop.append(col)
            except:
                columns_to_drop.append(col)

        X = X.drop(columns=[c for c in columns_to_drop if c in X.columns], errors='ignore')
        X = X.fillna(0)

        # Convert any remaining object columns
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = pd.Categorical(X[col]).codes

        return X

    @classmethod
    def _save_split(
        cls, split_id, X, y, merged,
        split_strategy, split_ratio, random_seed,
        dataset_id, prediction_window
    ):
        """Save the train/test split."""
        split_dir = FileManager.create_split_folder(split_id)

        if split_strategy == 'time_based':
            cutoff_date = pd.to_datetime('2024-11-01')
            train_mask = merged['date'] < cutoff_date
            test_mask = merged['date'] >= cutoff_date

            X_train = X[train_mask.values]
            X_test = X[test_mask.values]
            y_train = y[train_mask.values]
            y_test = y[test_mask.values]
        else:  # athlete_based
            splitter = GroupShuffleSplit(n_splits=1, test_size=split_ratio, random_state=random_seed)
            train_idx, test_idx = next(splitter.split(X, groups=merged['athlete_id']))

            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]

        # Save splits
        X_train.to_csv(os.path.join(split_dir, 'X_train.csv'), index=False)
        X_test.to_csv(os.path.join(split_dir, 'X_test.csv'), index=False)
        y_train.to_csv(os.path.join(split_dir, 'y_train.csv'), index=False)
        y_test.to_csv(os.path.join(split_dir, 'y_test.csv'), index=False)

        # Save metadata
        metadata = {
            'dataset_id': dataset_id,
            'split_strategy': split_strategy,
            'split_ratio': split_ratio,
            'prediction_window': prediction_window,
            'random_seed': random_seed,
            'created_at': datetime.utcnow().isoformat(),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': len(X_train.columns),
            'feature_names': list(X_train.columns),
            'class_distribution': {
                'train': {'injury': int(y_train.sum()), 'no_injury': int(len(y_train) - y_train.sum())},
                'test': {'injury': int(y_test.sum()), 'no_injury': int(len(y_test) - y_test.sum())}
            }
        }

        with open(os.path.join(split_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def get_preprocessing_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get preprocessing job status."""
        return ProgressTracker.get_job(job_id)

    @classmethod
    def list_splits(cls) -> List[Dict[str, Any]]:
        """List all available preprocessed splits."""
        return FileManager.list_splits()

    @classmethod
    def get_split(cls, split_id: str) -> Optional[Dict[str, Any]]:
        """Get split details."""
        processed_dir = current_app.config['PROCESSED_DATA_DIR']
        metadata_path = os.path.join(processed_dir, split_id, 'metadata.json')

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
