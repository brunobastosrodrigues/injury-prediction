import os
import sys
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import pandas as pd
import numpy as np
import random

from flask import current_app
from ..utils.progress_tracker import ProgressTracker
from ..utils.file_manager import FileManager


class DataGenerationService:
    """Service for generating synthetic athlete data."""

    @staticmethod
    def _setup_imports():
        """Set up imports from synthetic_data_generation module."""
        project_root = current_app.config.get('SYNTHETIC_DATA_MODULE')
        if project_root and project_root not in sys.path:
            sys.path.insert(0, project_root)

    @classmethod
    def generate_dataset_async(
        cls,
        n_athletes: int = 100,
        simulation_year: int = 2024,
        random_seed: int = 42,
        injury_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start async data generation and return job_id."""
        job_id = ProgressTracker.create_job('data_generation')

        # Start generation in background thread
        thread = threading.Thread(
            target=cls._run_generation,
            args=(job_id, n_athletes, simulation_year, random_seed, injury_config),
            daemon=True
        )
        thread.start()

        return job_id

    @classmethod
    def _run_generation(
        cls,
        job_id: str,
        n_athletes: int,
        simulation_year: int,
        random_seed: int,
        injury_config: Optional[Dict[str, Any]]
    ):
        """Run the actual data generation (in background thread)."""
        try:
            # Import here to avoid circular imports and ensure path is set
            from app import create_app
            app = create_app()

            with app.app_context():
                cls._setup_imports()

                # Set random seeds
                np.random.seed(random_seed)
                random.seed(random_seed)

                ProgressTracker.start_job(job_id, total_steps=n_athletes)
                ProgressTracker.update_progress(job_id, 0, 'Initializing...')

                # Import the simulation functions
                from simulate_year import simulate_full_year
                from logistics.athlete_profiles import generate_athlete_cohort

                # Generate athlete cohort
                ProgressTracker.update_progress(job_id, 1, 'Generating athlete profiles...')
                athletes = generate_athlete_cohort(n_athletes)

                # Simulate each athlete's year
                simulated_data = []
                for i, athlete in enumerate(athletes):
                    if not ProgressTracker.is_running(job_id):
                        ProgressTracker.cancel_job(job_id)
                        return

                    progress = int((i + 1) / n_athletes * 95)  # Reserve 5% for saving
                    ProgressTracker.update_progress(
                        job_id,
                        progress,
                        f'Simulating athlete {i + 1}/{n_athletes}...',
                        current_athlete=i + 1,
                        total_athletes=n_athletes
                    )

                    athlete_data = simulate_full_year(athlete, year=simulation_year)
                    simulated_data.append(athlete_data)

                # Save the data
                ProgressTracker.update_progress(job_id, 96, 'Saving data...')
                dataset_id = cls._save_dataset(
                    simulated_data,
                    n_athletes,
                    simulation_year,
                    random_seed,
                    injury_config
                )

                ProgressTracker.complete_job(job_id, result={'dataset_id': dataset_id})

        except Exception as e:
            ProgressTracker.fail_job(job_id, str(e))

    @classmethod
    def _save_dataset(
        cls,
        simulated_data: list,
        n_athletes: int,
        simulation_year: int,
        random_seed: int,
        injury_config: Optional[Dict[str, Any]]
    ) -> str:
        """Save simulation data to files and return dataset_id."""
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
        folder_path = FileManager.create_dataset_folder(dataset_id)

        # Process data into DataFrames
        athlete_profiles = []
        daily_data_records = []
        activity_data_records = []

        for athlete_data in simulated_data:
            athlete = athlete_data['athlete']

            # Athlete profile
            athlete_profiles.append({
                'athlete_id': athlete['id'],
                'gender': athlete['gender'],
                'age': athlete['age'],
                'height_cm': athlete['height'],
                'weight_kg': round(athlete['weight'], 1),
                'genetic_factor': round(athlete['genetic_factor'], 2),
                'hrv_baseline': athlete['hrv_baseline'],
                'hrv_range': athlete['hrv_range'],
                'max_hr': round(athlete['max_hr'], 1),
                'resting_hr': round(athlete['resting_hr'], 1),
                'lthr': round(athlete['lthr'], 1),
                'hr_zones': str(athlete['hr_zones']),
                'vo2max': round(athlete['vo2max'], 1),
                'running_threshold_pace': athlete['run_threshold_pace'],
                'ftp': round(athlete['ftp'], 1),
                'css': athlete['css'],
                'training_experience': athlete['training_experience'],
                'weekly_training_hours': round(athlete['weekly_training_hours'], 1),
                'recovery_rate': round(athlete['recovery_rate'], 2),
                'lifestyle': athlete['lifestyle'],
                'sleep_time_norm': athlete['sleep_time_norm'],
                'sleep_quality': athlete['sleep_quality'],
                'nutrition_factor': athlete['nutrition_factor'],
                'stress_factor': athlete['stress_factor'],
                'smoking_factor': athlete['smoking_factor'],
                'drinking_factor': athlete['drinking_factor']
            })

            # Daily data
            for daily_entry in athlete_data['daily_data']:
                daily_data_records.append({
                    'athlete_id': daily_entry['athlete_id'],
                    'date': daily_entry['date'],
                    'resting_hr': daily_entry['resting_hr'],
                    'hrv': daily_entry['hrv'],
                    'sleep_hours': daily_entry['sleep_hours'],
                    'deep_sleep': daily_entry['deep_sleep'],
                    'light_sleep': daily_entry['light_sleep'],
                    'rem_sleep': daily_entry['rem_sleep'],
                    'sleep_quality': daily_entry['sleep_quality'],
                    'body_battery_morning': daily_entry['body_battery_morning'],
                    'stress': daily_entry['stress'],
                    'body_battery_evening': daily_entry['body_battery_evening'],
                    'planned_tss': daily_entry['planned_tss'],
                    'actual_tss': daily_entry['actual_tss'],
                    'injury': daily_entry['injury']
                })

            # Activity data
            for activity_entry in athlete_data['activity_data']:
                if not activity_entry:
                    continue
                for sport_key, workout_data in activity_entry.items():
                    activity_data_records.append({
                        'athlete_id': workout_data['athlete_id'],
                        'date': workout_data['date'],
                        'sport': workout_data['sport'],
                        'workout_type': workout_data['workout_type'],
                        'duration_minutes': workout_data['duration_minutes'],
                        'tss': workout_data['tss'],
                        'intensity_factor': workout_data['intensity_factor'],
                        'avg_hr': workout_data.get('avg_hr'),
                        'max_hr': workout_data.get('max_hr'),
                        'hr_zones': str(workout_data.get('hr_zones')),
                        'distance_km': workout_data.get('distance_km'),
                        'avg_speed_kph': workout_data.get('avg_speed_kph'),
                        'avg_power': workout_data.get('avg_power'),
                        'normalized_power': workout_data.get('normalized_power'),
                        'power_zones': str(workout_data.get('power_zones')),
                        'intensity_variability': workout_data.get('intensity_variability'),
                        'work_kilojoules': workout_data.get('work_kilojoules'),
                        'elevation_gain': workout_data.get('elevation_gain'),
                        'avg_pace_min_km': workout_data.get('avg_pace_min_km'),
                        'training_effect_aerobic': workout_data.get('training_effect_aerobic'),
                        'training_effect_anaerobic': workout_data.get('training_effect_anaerobic'),
                        'distance_m': workout_data.get('distance_m'),
                        'avg_pace_min_100m': workout_data.get('avg_pace_min_100m')
                    })

        # Save CSVs
        df_athletes = pd.DataFrame(athlete_profiles)
        df_daily_data = pd.DataFrame(daily_data_records)
        df_activity_data = pd.DataFrame(activity_data_records)

        df_athletes.to_csv(os.path.join(folder_path, 'athletes.csv'), index=False)
        df_daily_data.to_csv(os.path.join(folder_path, 'daily_data.csv'), index=False)
        df_activity_data.to_csv(os.path.join(folder_path, 'activity_data.csv'), index=False)

        # Save metadata
        metadata = {
            'n_athletes': n_athletes,
            'simulation_year': simulation_year,
            'random_seed': random_seed,
            'injury_config': injury_config,
            'created_at': datetime.utcnow().isoformat(),
            'n_daily_records': len(daily_data_records),
            'n_activities': len(activity_data_records),
            'injury_rate': df_daily_data['injury'].mean() if len(df_daily_data) > 0 else 0
        }
        FileManager.save_dataset_metadata(dataset_id, metadata)

        return dataset_id

    @classmethod
    def get_generation_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a data generation job."""
        return ProgressTracker.get_job(job_id)

    @classmethod
    def cancel_generation(cls, job_id: str) -> bool:
        """Cancel a running data generation job."""
        job = ProgressTracker.get_job(job_id)
        if job and job['status'] == 'running':
            ProgressTracker.cancel_job(job_id)
            return True
        return False

    @classmethod
    def list_datasets(cls) -> list:
        """List all available datasets."""
        return FileManager.list_datasets()

    @classmethod
    def get_dataset(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset details and summary."""
        return FileManager.get_dataset_summary(dataset_id)

    @classmethod
    def delete_dataset(cls, dataset_id: str) -> bool:
        """Delete a dataset."""
        return FileManager.delete_dataset(dataset_id)

    @classmethod
    def get_dataset_sample(cls, dataset_id: str, table: str = 'daily_data', n_rows: int = 100) -> Optional[Dict[str, Any]]:
        """Get a sample of data from a dataset."""
        from flask import current_app
        folder_path = os.path.join(current_app.config['RAW_DATA_DIR'], dataset_id)
        file_path = os.path.join(folder_path, f'{table}.csv')

        if not os.path.exists(file_path):
            return None

        df = pd.read_csv(file_path, nrows=n_rows)
        return {
            'columns': list(df.columns),
            'data': df.to_dict(orient='records'),
            'total_rows': sum(1 for _ in open(file_path)) - 1  # Subtract header
        }
