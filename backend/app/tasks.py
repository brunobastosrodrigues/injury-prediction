from .celery_app import celery_app
from .utils.progress_tracker import ProgressTracker
from .utils.file_manager import FileManager
from typing import Dict, Any, Optional, List
import numpy as np
import random
import os
import uuid
from datetime import datetime

@celery_app.task(name='generate_dataset')
def generate_dataset_task(job_id: str, n_athletes: int, simulation_year: int, random_seed: int, injury_config: Optional[Dict[str, Any]]):
    """Celery task for generating synthetic athlete data."""
    from app import create_app
    from .services.data_generation_service import DataGenerationService
    app = create_app()
    with app.app_context():
        try:
            np.random.seed(random_seed)
            random.seed(random_seed)
            ProgressTracker.start_job(job_id, total_steps=n_athletes)
            ProgressTracker.update_progress(job_id, 0, 'Initializing...')

            from synthetic_data_generation.simulate_year import simulate_full_year
            from synthetic_data_generation.logistics.athlete_profiles import generate_athlete_cohort

            athletes = generate_athlete_cohort(n_athletes)
            simulated_data = []
            for i, athlete in enumerate(athletes):
                if not ProgressTracker.is_running(job_id):
                    ProgressTracker.cancel_job(job_id)
                    return
                progress = int((i + 1) / n_athletes * 95)
                ProgressTracker.update_progress(job_id, progress, f'Simulating athlete {i + 1}/{n_athletes}...', current_athlete=i + 1, total_athletes=n_athletes)
                athlete_data = simulate_full_year(athlete, year=simulation_year)
                simulated_data.append(athlete_data)

            ProgressTracker.update_progress(job_id, 96, 'Saving data...')
            dataset_id = DataGenerationService._save_dataset(simulated_data, n_athletes, simulation_year, random_seed, injury_config)
            ProgressTracker.complete_job(job_id, result={'dataset_id': dataset_id})
        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")

@celery_app.task(name='preprocess_dataset')
def preprocess_dataset_task(job_id: str, dataset_id: str, split_strategy: str, split_ratio: float, prediction_window: int, random_seed: int):
    """Celery task for preprocessing and feature engineering."""
    from app import create_app
    from .services.preprocessing_service import PreprocessingService
    app = create_app()
    with app.app_context():
        try:
            ProgressTracker.start_job(job_id, total_steps=6)
            ProgressTracker.update_progress(job_id, 10, 'Loading data...')
            raw_dir = app.config['RAW_DATA_DIR']
            dataset_path = os.path.join(raw_dir, dataset_id)

            athletes_df = FileManager.read_df(os.path.join(dataset_path, 'athletes'))
            daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
            activity_df = FileManager.read_df(os.path.join(dataset_path, 'activity_data'))

            ProgressTracker.update_progress(job_id, 20, 'Merging data...')
            merged = PreprocessingService._merge_data(athletes_df, daily_df, activity_df)

            ProgressTracker.update_progress(job_id, 35, 'Engineering injury labels...')
            labeled_df = PreprocessingService._engineer_injury_labels(merged, prediction_window)
            import pandas as pd
            targets_df = PreprocessingService._create_prediction_targets(labeled_df, prediction_window)

            ProgressTracker.update_progress(job_id, 50, 'Engineering features...')
            X = targets_df.drop(['injury', 'injury_onset', 'recovery_day', 'pre_injury', 'injury_state', 'will_get_injured', 'time_to_injury'], axis=1, errors='ignore')
            y = targets_df['will_get_injured']
            X_engineered = PreprocessingService._engineer_features(X)

            ProgressTracker.update_progress(job_id, 70, 'Encoding features...')
            X_encoded = PreprocessingService._encode_categorical(X_engineered)

            ProgressTracker.update_progress(job_id, 85, 'Splitting data...')
            split_id = f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
            PreprocessingService._save_split(split_id, X_encoded, y, merged, split_strategy, split_ratio, random_seed, dataset_id, prediction_window)
            ProgressTracker.complete_job(job_id, result={'split_id': split_id})
        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")

@celery_app.task(name='train_models')
def train_models_task(job_id: str, split_id: str, model_types: List[str], hyperparameters: Optional[Dict[str, Dict]]):
    """Celery task for model training."""
    from app import create_app
    from .services.training_service import TrainingService
    app = create_app()
    with app.app_context():
        try:
            total_steps = len(model_types) * 2
            ProgressTracker.start_job(job_id, total_steps=total_steps)
            ProgressTracker.update_progress(job_id, 5, 'Loading data...')
            processed_dir = app.config['PROCESSED_DATA_DIR']
            split_dir = os.path.join(processed_dir, split_id)

            X_train = FileManager.read_df(os.path.join(split_dir, 'X_train'))
            X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
            y_train = FileManager.read_df(os.path.join(split_dir, 'y_train')).values.ravel()
            y_test = FileManager.read_df(os.path.join(split_dir, 'y_test')).values.ravel()

            trained_models = []
            for i, model_type in enumerate(model_types):
                step = (i + 1) / len(model_types) * 80 + 10
                ProgressTracker.update_progress(job_id, int(step), f'Training {TrainingService.get_model_types().get(model_type, {}).get("name", model_type)}...')
                params = TrainingService.get_model_types().get(model_type, {}).get('default_params', {}).copy()
                if hyperparameters and model_type in hyperparameters:
                    params.update(hyperparameters[model_type])
                model = TrainingService._create_model(model_type, params)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                metrics = TrainingService._calculate_metrics(y_test, y_pred, y_pred_proba)
                feature_importance = TrainingService._get_feature_importance(model, X_train.columns, model_type)
                model_id = f"model_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
                TrainingService._save_model(model_id, model, model_type, params, metrics, feature_importance, split_id, X_test.columns.tolist())
                trained_models.append({'model_id': model_id, 'model_type': model_type, 'metrics': metrics})
            ProgressTracker.complete_job(job_id, result={'models': trained_models})
        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")

@celery_app.task(name='ingest_real_data')
def ingest_real_data_task(job_id: str, dataset_id: str, file_path: str, data_type: str):
    """Celery task for ingesting real-world athlete data."""
    from app import create_app
    from .services.ingestion_service import IngestionService
    app = create_app()
    with app.app_context():
        try:
            ProgressTracker.start_job(job_id, total_steps=3)
            ProgressTracker.update_progress(job_id, 33, 'Processing real data...')
            
            real_df = IngestionService.process_real_data(file_path, data_type)
            
            ProgressTracker.update_progress(job_id, 66, 'Merging into dataset...')
            # Create a virtual athlete ID for real data
            athlete_id = f"real_athlete_{uuid.uuid4().hex[:6]}"
            IngestionService.merge_real_into_dataset(dataset_id, real_df, athlete_id)
            
            ProgressTracker.update_progress(job_id, 100, 'Ingestion complete.')
            ProgressTracker.complete_job(job_id, result={'athlete_id': athlete_id})
            
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")