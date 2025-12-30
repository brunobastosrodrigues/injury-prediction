"""
PMData Adapter - Loads and unifies PMData for Sim2Real validation.

This adapter extracts:
1. Wellness data (sleep, stress, fatigue, soreness, recovery)
2. Training Load data (sRPE, active minutes)
3. ACWR (Acute:Chronic Workload Ratio)
4. Injury labels

The combination of wellness (vulnerability) and load (trigger) features
provides the complete picture for injury prediction.
"""

import pandas as pd
import os
import json
import glob
from datetime import timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PMDataAdapter:
    def __init__(self, pmdata_path):
        self.root_path = pmdata_path

    def _load_wellness_data(self):
        """Load subjective wellness data (sleep, stress, fatigue, etc.)."""
        wellness_files = glob.glob(os.path.join(self.root_path, '*', 'pmsys', 'wellness.csv'))

        all_wellness = []
        for f in wellness_files:
            parts = f.split(os.sep)
            try:
                p_idx = parts.index('pmsys')
                participant_id = parts[p_idx - 1]
            except ValueError:
                participant_id = 'unknown'

            df = pd.read_csv(f)
            df['athlete_id'] = participant_id
            all_wellness.append(df)

        if not all_wellness:
            raise ValueError(f"No wellness.csv files found in {self.root_path}")

        wellness_df = pd.concat(all_wellness, ignore_index=True)

        # Standardize date
        if 'effective_time_frame' in wellness_df.columns:
            wellness_df['date'] = pd.to_datetime(wellness_df['effective_time_frame']).dt.date
        elif 'date' in wellness_df.columns:
            wellness_df['date'] = pd.to_datetime(wellness_df['date']).dt.date

        return wellness_df

    def _load_injury_data(self):
        """Load injury records."""
        injury_files = glob.glob(os.path.join(self.root_path, '*', 'pmsys', 'injury.csv'))

        all_injuries = []
        for f in injury_files:
            parts = f.split(os.sep)
            try:
                p_idx = parts.index('pmsys')
                participant_id = parts[p_idx - 1]
            except ValueError:
                participant_id = 'unknown'

            df = pd.read_csv(f)
            df['athlete_id'] = participant_id
            all_injuries.append(df)

        if all_injuries:
            injury_df = pd.concat(all_injuries, ignore_index=True)
            if 'effective_time_frame' in injury_df.columns:
                injury_df['date'] = pd.to_datetime(injury_df['effective_time_frame']).dt.date
            elif 'date' in injury_df.columns:
                injury_df['date'] = pd.to_datetime(injury_df['date']).dt.date
        else:
            injury_df = pd.DataFrame(columns=['athlete_id', 'date'])

        return injury_df

    def _load_srpe_data(self):
        """
        Load Session RPE (sRPE) data - the gold standard for training load.

        sRPE Load = RPE (1-10) × Duration (minutes)
        """
        srpe_files = glob.glob(os.path.join(self.root_path, '*', 'pmsys', 'srpe.csv'))

        all_srpe = []
        for f in srpe_files:
            parts = f.split(os.sep)
            try:
                p_idx = parts.index('pmsys')
                participant_id = parts[p_idx - 1]
            except ValueError:
                participant_id = 'unknown'

            try:
                df = pd.read_csv(f)
                df['athlete_id'] = participant_id
                df['datetime'] = pd.to_datetime(df['end_date_time'])
                df['date'] = df['datetime'].dt.date
                # Calculate sRPE Load
                df['srpe_load'] = df['perceived_exertion'] * df['duration_min']
                all_srpe.append(df)
            except (pd.errors.EmptyDataError, pd.errors.ParserError, KeyError) as e:
                logger.warning(f"Skipping sRPE file {f}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error reading sRPE file {f}: {e}")

        if all_srpe:
            return pd.concat(all_srpe, ignore_index=True)
        return pd.DataFrame()

    def _load_fitbit_activity(self):
        """
        Load Fitbit activity data (very active minutes, moderately active minutes).

        These serve as a proxy for training load when sRPE is not available.
        """
        all_data = []

        athlete_dirs = glob.glob(os.path.join(self.root_path, 'p*'))

        for athlete_dir in athlete_dirs:
            athlete_id = os.path.basename(athlete_dir)
            fitbit_dir = os.path.join(athlete_dir, 'fitbit')

            if not os.path.exists(fitbit_dir):
                continue

            daily_metrics = {}

            # Very active minutes
            vam_file = os.path.join(fitbit_dir, 'very_active_minutes.json')
            if os.path.exists(vam_file):
                try:
                    with open(vam_file, 'r') as f:
                        data = json.load(f)
                        for entry in data:
                            date = pd.to_datetime(entry['dateTime']).date()
                            if date not in daily_metrics:
                                daily_metrics[date] = {'athlete_id': athlete_id}
                            daily_metrics[date]['very_active_min'] = int(entry['value'])
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping very_active_minutes for {athlete_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error reading {vam_file}: {e}")

            # Moderately active minutes
            mam_file = os.path.join(fitbit_dir, 'moderately_active_minutes.json')
            if os.path.exists(mam_file):
                try:
                    with open(mam_file, 'r') as f:
                        data = json.load(f)
                        for entry in data:
                            date = pd.to_datetime(entry['dateTime']).date()
                            if date not in daily_metrics:
                                daily_metrics[date] = {'athlete_id': athlete_id}
                            daily_metrics[date]['moderately_active_min'] = int(entry['value'])
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping moderately_active_minutes for {athlete_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error reading {mam_file}: {e}")

            # Convert to list
            for date, metrics in daily_metrics.items():
                metrics['date'] = date
                all_data.append(metrics)

        if all_data:
            df = pd.DataFrame(all_data)
            df['very_active_min'] = df.get('very_active_min', 0).fillna(0)
            df['moderately_active_min'] = df.get('moderately_active_min', 0).fillna(0)
            df['total_active_min'] = df['very_active_min'] + df['moderately_active_min']
            return df

        return pd.DataFrame()

    def _calculate_daily_load(self, srpe_df, fitbit_df):
        """
        Calculate daily training load from multiple sources.

        Primary: sRPE Load (RPE × Duration) - scientifically validated
        Secondary: Active Minutes (when sRPE missing) - Fitbit proxy
        """
        # Aggregate sRPE by date (sum all sessions per day)
        if not srpe_df.empty:
            daily_srpe = srpe_df.groupby(['athlete_id', 'date']).agg({
                'srpe_load': 'sum',
                'duration_min': 'sum',
                'perceived_exertion': 'mean'
            }).reset_index()
            daily_srpe.columns = ['athlete_id', 'date', 'daily_srpe_load', 'daily_duration', 'avg_rpe']
        else:
            daily_srpe = pd.DataFrame(columns=['athlete_id', 'date', 'daily_srpe_load'])

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
        # Priority: sRPE Load > Active Minutes (scaled)
        daily_load['daily_load'] = daily_load.get('daily_srpe_load', 0)
        if 'daily_srpe_load' in daily_load.columns:
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

    def _calculate_acwr(self, df, load_col='daily_load', acute_days=7, chronic_days=28):
        """
        Calculate Acute:Chronic Workload Ratio (ACWR).

        ACWR = (7-day rolling mean) / (28-day rolling mean)

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

            # Fill missing dates to ensure continuous time series
            if len(group) > 0:
                date_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
                group = group.reindex(date_range)
                group['athlete_id'] = athlete_id
                group[load_col] = group[load_col].fillna(0)

            # Calculate rolling averages
            group['acute_load'] = group[load_col].rolling(window=acute_days, min_periods=1).mean()
            group['chronic_load'] = group[load_col].rolling(window=chronic_days, min_periods=7).mean()

            # Calculate ACWR (avoid division by zero)
            group['acwr'] = group['acute_load'] / (group['chronic_load'] + 1e-6)

            # Cap extreme ACWR values
            group['acwr'] = group['acwr'].clip(0, 4)

            # Calculate week-over-week load change
            group['load_change_7d'] = (
                group[load_col].rolling(7).sum() /
                (group[load_col].shift(7).rolling(7).sum() + 1e-6)
            ).clip(0, 5)

            group = group.reset_index()
            group = group.rename(columns={'index': 'date'})
            result.append(group)

        if result:
            return pd.concat(result, ignore_index=True)
        return df

    def load_and_unify(self, injury_window_days=3, include_load=True):
        """
        Load and unify all PMData sources into a single DataFrame.

        Args:
            injury_window_days: Days ahead to look for injury (default 3)
            include_load: Whether to include training load and ACWR features

        Returns:
            DataFrame with wellness, load, and injury features
        """
        logger.info(f"Loading PMData from: {self.root_path}")

        # 1. Load wellness data
        wellness_df = self._load_wellness_data()

        # 2. Load injury data
        injury_df = self._load_injury_data()

        # 3. Mark injury days
        injury_set = set(zip(injury_df['athlete_id'], injury_df['date']))
        wellness_df['is_injured'] = wellness_df.apply(
            lambda row: 1 if (row['athlete_id'], row['date']) in injury_set else 0, axis=1
        )

        # 4. Create forward-looking injury target
        def calculate_target(group, window=injury_window_days):
            group = group.sort_values('date')
            indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=window)
            group['will_get_injured'] = group['is_injured'].rolling(window=indexer, min_periods=1).max()
            return group

        # Apply target calculation per athlete
        result_dfs = []
        for athlete_id, group in wellness_df.groupby('athlete_id'):
            group_result = calculate_target(group.copy(), injury_window_days)
            result_dfs.append(group_result)
        wellness_df = pd.concat(result_dfs, ignore_index=True)

        # 5. Rename wellness columns to standard schema
        rename_map = {
            'sleep_quality': 'sleep_quality_daily',
            'readiness': 'recovery_score',
            'stress': 'stress_score',
            'sleep_duration_h': 'sleep_hours',
            'fatigue': 'fatigue_score',
            'mood': 'mood_score',
            'soreness': 'soreness_score',
        }
        df_adapted = wellness_df.rename(columns=rename_map)

        # 6. Normalize wellness features to 0-1
        wellness_features = ['sleep_quality_daily', 'stress_score', 'recovery_score',
                             'fatigue_score', 'mood_score', 'soreness_score', 'sleep_hours']
        for feat in wellness_features:
            if feat in df_adapted.columns:
                feat_max = df_adapted[feat].max()
                feat_min = df_adapted[feat].min()
                if feat_max > feat_min:
                    df_adapted[feat] = (df_adapted[feat] - feat_min) / (feat_max - feat_min + 1e-8)

        # 7. Load and merge training load data
        if include_load:
            srpe_df = self._load_srpe_data()
            fitbit_df = self._load_fitbit_activity()

            if not srpe_df.empty or not fitbit_df.empty:
                # Calculate daily load
                daily_load = self._calculate_daily_load(srpe_df, fitbit_df)

                # Calculate ACWR
                load_with_acwr = self._calculate_acwr(daily_load)

                # Ensure date columns match
                load_with_acwr['date'] = pd.to_datetime(load_with_acwr['date']).dt.date
                df_adapted['date'] = pd.to_datetime(df_adapted['date']).dt.date

                # Select load columns to merge
                load_cols = ['athlete_id', 'date', 'daily_load', 'acute_load', 'chronic_load', 'acwr']
                available_load_cols = [c for c in load_cols if c in load_with_acwr.columns]

                # Merge load data with wellness
                df_adapted = pd.merge(
                    df_adapted,
                    load_with_acwr[available_load_cols],
                    on=['athlete_id', 'date'],
                    how='left'
                )

                # Normalize load features to 0-1 (per athlete for better comparison)
                load_features = ['daily_load', 'acute_load', 'chronic_load']
                for feat in load_features:
                    if feat in df_adapted.columns:
                        feat_max = df_adapted[feat].max()
                        feat_min = df_adapted[feat].min()
                        if feat_max > feat_min:
                            df_adapted[f'{feat}_norm'] = (
                                (df_adapted[feat] - feat_min) / (feat_max - feat_min + 1e-8)
                            )

                # ACWR is already a ratio, just clip it to reasonable range
                if 'acwr' in df_adapted.columns:
                    df_adapted['acwr'] = df_adapted['acwr'].clip(0, 4)

        # 8. Select final columns
        all_feature_cols = [
            'date', 'athlete_id',
            # Wellness features
            'sleep_quality_daily', 'stress_score', 'recovery_score',
            'fatigue_score', 'mood_score', 'soreness_score', 'sleep_hours',
            # Load features
            'daily_load', 'acute_load', 'chronic_load', 'acwr',
            'daily_load_norm', 'acute_load_norm', 'chronic_load_norm',
            # Target
            'is_injured', 'will_get_injured'
        ]
        available_cols = [c for c in all_feature_cols if c in df_adapted.columns]

        result_df = df_adapted[available_cols].copy()

        return result_df.dropna(subset=['will_get_injured'])
