from .celery_app import celery_app
from .utils.progress_tracker import ProgressTracker
from .utils.file_manager import FileManager
from typing import Dict, Any, Optional, List
import numpy as np
import random
import os
import uuid
import subprocess
import json
import shutil
from datetime import datetime

# Path to Rust binary - can be overridden by environment variable
RUST_DATAGEN_BINARY = os.environ.get(
    'DATAGEN_BINARY',
    os.path.join(os.path.dirname(__file__), '..', '..', 'injury-prediction-datagen', 'target', 'release', 'datagen')
)

# Fallback to Python if Rust binary not available
USE_RUST_DATAGEN = os.path.exists(RUST_DATAGEN_BINARY)


@celery_app.task(name='generate_dataset')
def generate_dataset_task(job_id: str, n_athletes: int, simulation_year: int, random_seed: int, injury_config: Optional[Dict[str, Any]]):
    """Celery task for generating synthetic athlete data.

    Uses Rust binary for 1000x faster generation if available, otherwise falls back to Python.
    """
    from app import create_app
    from .services.data_generation_service import DataGenerationService
    app = create_app()
    with app.app_context():
        try:
            ProgressTracker.start_job(job_id, total_steps=n_athletes)
            ProgressTracker.update_progress(job_id, 0, 'Initializing...')

            if USE_RUST_DATAGEN:
                # Use fast Rust implementation
                dataset_id = _generate_with_rust(job_id, n_athletes, simulation_year, random_seed, injury_config, app)
            else:
                # Fallback to Python implementation
                dataset_id = _generate_with_python(job_id, n_athletes, simulation_year, random_seed, injury_config, app)

            ProgressTracker.complete_job(job_id, result={'dataset_id': dataset_id})
        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")


def _generate_with_rust(job_id: str, n_athletes: int, simulation_year: int, random_seed: int,
                        injury_config: Optional[Dict[str, Any]], app) -> str:
    """Generate dataset using fast Rust binary."""
    dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    output_dir = os.path.join(app.config['RAW_DATA_DIR'], dataset_id)
    os.makedirs(output_dir, exist_ok=True)

    ProgressTracker.update_progress(job_id, 5, 'Starting Rust data generator...')

    # Build command with base arguments
    cmd = [
        RUST_DATAGEN_BINARY,
        '--n-athletes', str(n_athletes),
        '--year', str(simulation_year),
        '--seed', str(random_seed),
        '--output-dir', output_dir,
        '--json-progress',
        '--no-progress',
    ]

    # Add configuration parameters if provided
    if injury_config:
        # Injury model parameters
        if 'acwr_danger_threshold' in injury_config:
            cmd.extend(['--acwr-danger', str(injury_config['acwr_danger_threshold'])])
        if 'acwr_caution_threshold' in injury_config:
            cmd.extend(['--acwr-caution', str(injury_config['acwr_caution_threshold'])])
        if 'acwr_undertrained_threshold' in injury_config:
            cmd.extend(['--acwr-undertrained', str(injury_config['acwr_undertrained_threshold'])])
        if 'base_injury_probability' in injury_config:
            cmd.extend(['--base-injury-prob', str(injury_config['base_injury_probability'])])
        if 'max_injury_probability' in injury_config:
            cmd.extend(['--max-injury-prob', str(injury_config['max_injury_probability'])])

        # Training model parameters
        if 'ctl_time_constant' in injury_config:
            cmd.extend(['--ctl-days', str(injury_config['ctl_time_constant'])])
        if 'atl_time_constant' in injury_config:
            cmd.extend(['--atl-days', str(injury_config['atl_time_constant'])])
        if 'acwr_acute_window' in injury_config:
            cmd.extend(['--acwr-acute-window', str(injury_config['acwr_acute_window'])])
        if 'acwr_chronic_window' in injury_config:
            cmd.extend(['--acwr-chronic-window', str(injury_config['acwr_chronic_window'])])

        # Athlete generation parameters
        if 'min_age' in injury_config:
            cmd.extend(['--min-age', str(injury_config['min_age'])])
        if 'max_age' in injury_config:
            cmd.extend(['--max-age', str(injury_config['max_age'])])
        if 'min_weekly_hours' in injury_config:
            cmd.extend(['--min-hours', str(injury_config['min_weekly_hours'])])
        if 'max_weekly_hours' in injury_config:
            cmd.extend(['--max-hours', str(injury_config['max_weekly_hours'])])
        if 'female_probability' in injury_config:
            cmd.extend(['--female-prob', str(injury_config['female_probability'])])

    # Run Rust binary with JSON progress output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Stream progress from stderr
    for line in process.stderr:
        line = line.strip()
        if not line:
            continue
        try:
            progress_data = json.loads(line)
            completed = progress_data.get('progress', 0)
            total = progress_data.get('total', n_athletes)
            pct = int(90 * completed / total) + 5  # 5-95% range
            ProgressTracker.update_progress(
                job_id, pct,
                f'Simulating athlete {completed}/{total}...',
                current_athlete=completed,
                total_athletes=total
            )
        except (json.JSONDecodeError, KeyError):
            pass

    process.wait()

    if process.returncode != 0:
        stdout, stderr = process.communicate()
        raise RuntimeError(f"Rust datagen failed with code {process.returncode}: {stderr}")

    ProgressTracker.update_progress(job_id, 96, 'Finalizing data files...')

    # Rename files to match expected naming convention
    rust_to_python_names = {
        'athlete_profiles.parquet': 'athletes.parquet',
        'daily_data.parquet': 'daily_data.parquet',
        'activity_data.parquet': 'activity_data.parquet',
    }

    for rust_name, python_name in rust_to_python_names.items():
        rust_path = os.path.join(output_dir, rust_name)
        python_path = os.path.join(output_dir, python_name)
        if os.path.exists(rust_path) and rust_name != python_name:
            shutil.move(rust_path, python_path)

    # Read and update metadata
    metadata_path = os.path.join(output_dir, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            rust_metadata = json.load(f)
    else:
        rust_metadata = {}

    # Merge with our metadata format
    metadata = {
        'n_athletes': n_athletes,
        'simulation_year': simulation_year,
        'random_seed': random_seed,
        'injury_config': injury_config,
        'created_at': datetime.utcnow().isoformat(),
        'n_daily_records': rust_metadata.get('n_daily_records', 0),
        'n_activities': rust_metadata.get('n_activities', 0),
        'injury_rate': rust_metadata.get('injury_rate', 0) / 100.0,  # Convert from percentage
        'generator': 'rust',
    }
    FileManager.save_dataset_metadata(dataset_id, metadata)

    return dataset_id


def _generate_with_python(job_id: str, n_athletes: int, simulation_year: int, random_seed: int,
                          injury_config: Optional[Dict[str, Any]], app) -> str:
    """Generate dataset using Python implementation (fallback)."""
    from .services.data_generation_service import DataGenerationService

    np.random.seed(random_seed)
    random.seed(random_seed)

    from synthetic_data_generation.simulate_year import simulate_full_year
    from synthetic_data_generation.logistics.athlete_profiles import generate_athlete_cohort

    athletes = generate_athlete_cohort(n_athletes)
    simulated_data = []
    for i, athlete in enumerate(athletes):
        if not ProgressTracker.is_running(job_id):
            ProgressTracker.cancel_job(job_id)
            raise RuntimeError("Job cancelled")
        progress = int((i + 1) / n_athletes * 95)
        ProgressTracker.update_progress(
            job_id, progress,
            f'Simulating athlete {i + 1}/{n_athletes}...',
            current_athlete=i + 1,
            total_athletes=n_athletes
        )
        athlete_data = simulate_full_year(athlete, year=simulation_year)
        simulated_data.append(athlete_data)

    ProgressTracker.update_progress(job_id, 96, 'Saving data...')
    dataset_id = DataGenerationService._save_dataset(
        simulated_data, n_athletes, simulation_year, random_seed, injury_config
    )

    return dataset_id

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


@celery_app.task(name='run_validation')
def run_validation_task(job_id: str, dataset_id: str):
    """Celery task for running external validation (Sim2Real).

    Compares a synthetic dataset against real PMData, computing:
    - Distribution alignment (JS divergence)
    - Sim2Real transfer learning
    - Causal mechanism analysis
    - Three Pillars of Validity

    Results are cached to /data/validation/<dataset_id>/
    """
    from app import create_app
    from .services.validation_service import ValidationService
    app = create_app()
    with app.app_context():
        try:
            ProgressTracker.start_job(job_id, total_steps=100)
            ProgressTracker.update_progress(job_id, 5, 'Loading datasets...', dataset_id=dataset_id)

            # Create validation results directory
            validation_dir = os.path.join(app.config.get('BASE_DIR', '/data'), 'data', 'validation', dataset_id)
            os.makedirs(validation_dir, exist_ok=True)

            # Step 1: Distribution comparison (20%)
            ProgressTracker.update_progress(job_id, 10, 'Computing distribution alignment...')
            distributions = ValidationService.get_distribution_comparison_for_dataset(dataset_id)
            _save_validation_result(validation_dir, 'distributions.json', distributions)
            ProgressTracker.update_progress(job_id, 25, 'Distribution comparison complete')

            # Step 2: Sim2Real transfer learning (40%)
            ProgressTracker.update_progress(job_id, 30, 'Running Sim2Real transfer experiment...')
            sim2real = ValidationService.run_sim2real_for_dataset(dataset_id)
            _save_validation_result(validation_dir, 'sim2real.json', sim2real)
            ProgressTracker.update_progress(job_id, 50, 'Sim2Real transfer complete')

            # Step 3: PMData analysis (20%)
            ProgressTracker.update_progress(job_id, 55, 'Analyzing PMData patterns...')
            pmdata_analysis = ValidationService.get_pmdata_analysis()
            _save_validation_result(validation_dir, 'pmdata_analysis.json', pmdata_analysis)
            ProgressTracker.update_progress(job_id, 65, 'PMData analysis complete')

            # Step 4: Causal mechanism analysis (20%)
            ProgressTracker.update_progress(job_id, 70, 'Computing causal mechanism analysis...')
            causal = ValidationService.get_causal_mechanism_for_dataset(dataset_id)
            _save_validation_result(validation_dir, 'causal_mechanism.json', causal)
            ProgressTracker.update_progress(job_id, 85, 'Causal mechanism complete')

            # Step 5: Three Pillars summary (5%)
            ProgressTracker.update_progress(job_id, 90, 'Computing Three Pillars summary...')
            three_pillars = ValidationService.get_three_pillars_for_dataset(dataset_id)
            _save_validation_result(validation_dir, 'three_pillars.json', three_pillars)

            # Step 6: Create overall summary
            ProgressTracker.update_progress(job_id, 95, 'Generating summary...')
            summary = {
                'dataset_id': dataset_id,
                'computed_at': datetime.utcnow().isoformat(),
                'overall_score': three_pillars.get('overall_score', 0),
                'pillars_passing': three_pillars.get('pillars_passing', '0/3'),
                'ready_for_publication': three_pillars.get('ready_for_publication', False),
                'sim2real_auc': sim2real.get('auc', 0),
                'avg_js_divergence': _calculate_avg_js(distributions),
            }
            _save_validation_result(validation_dir, 'summary.json', summary)

            ProgressTracker.complete_job(job_id, result={
                'dataset_id': dataset_id,
                'validation_dir': validation_dir,
                'summary': summary
            })

        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")


def _save_validation_result(validation_dir: str, filename: str, data: dict):
    """Save validation result to JSON file."""
    filepath = os.path.join(validation_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _calculate_avg_js(distributions: dict) -> float:
    """Calculate average JS divergence from distribution results."""
    if 'features' not in distributions:
        return 1.0
    js_values = [
        f.get('js_divergence', 1.0)
        for f in distributions.get('features', {}).values()
        if isinstance(f, dict) and 'js_divergence' in f
    ]
    return sum(js_values) / len(js_values) if js_values else 1.0


@celery_app.task(name='run_methodology_validation')
def run_methodology_validation_task(job_id: str, dataset_id: str, validation_types: list):
    """
    Celery task for running methodology validation suite.

    Supports:
    - 'loso': Leave-One-Subject-Out Cross-Validation
    - 'sensitivity': Sensitivity Analysis with Tornado Plot
    - 'equivalence': Rust-Python Equivalence Check
    """
    from app import create_app
    from .services.methodology_validation import MethodologyValidationService
    app = create_app()
    with app.app_context():
        try:
            total_steps = len(validation_types)
            ProgressTracker.start_job(job_id, total_steps=total_steps * 100)
            ProgressTracker.update_progress(job_id, 5, 'Starting methodology validation...')

            results = {
                'dataset_id': dataset_id,
                'validation_types': validation_types,
                'results': {}
            }

            for i, val_type in enumerate(validation_types):
                base_progress = (i / total_steps) * 100

                if val_type == 'loso':
                    ProgressTracker.update_progress(
                        job_id, int(base_progress + 5),
                        'Running LOSO Cross-Validation...'
                    )

                    def loso_progress(fold, total, fold_result):
                        pct = int(base_progress + 5 + (fold / total) * (100 / total_steps - 10))
                        ProgressTracker.update_progress(
                            job_id, pct,
                            f'LOSO Fold {fold}/{total}: AUC={fold_result["auc"]:.3f}'
                        )

                    loso_result = MethodologyValidationService.run_loso_validation(
                        dataset_id,
                        progress_callback=loso_progress
                    )
                    results['results']['loso'] = loso_result
                    MethodologyValidationService.save_validation_results(
                        dataset_id, 'loso', loso_result
                    )

                elif val_type == 'sensitivity':
                    ProgressTracker.update_progress(
                        job_id, int(base_progress + 5),
                        'Running Sensitivity Analysis...'
                    )

                    def sens_progress(param_idx, total, msg):
                        pct = int(base_progress + 5 + (param_idx / total) * (100 / total_steps - 10))
                        ProgressTracker.update_progress(job_id, pct, msg)

                    sens_result = MethodologyValidationService.run_sensitivity_analysis(
                        dataset_id,
                        progress_callback=sens_progress
                    )
                    results['results']['sensitivity'] = sens_result
                    MethodologyValidationService.save_validation_results(
                        dataset_id, 'sensitivity', sens_result
                    )

                elif val_type == 'equivalence':
                    ProgressTracker.update_progress(
                        job_id, int(base_progress + 5),
                        'Running Rust-Python Equivalence Check...'
                    )

                    def equiv_progress(step, total, msg):
                        pct = int(base_progress + 5 + (step / total) * (100 / total_steps - 10))
                        ProgressTracker.update_progress(job_id, pct, msg)

                    equiv_result = MethodologyValidationService.run_rust_python_equivalence(
                        progress_callback=equiv_progress
                    )
                    results['results']['equivalence'] = equiv_result
                    MethodologyValidationService.save_validation_results(
                        dataset_id, 'equivalence', equiv_result
                    )

            ProgressTracker.complete_job(job_id, result=results)

        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")


@celery_app.task(name='run_scientific_validation')
def run_scientific_validation_task(job_id: str, dataset_id: str, tasks: List[str]):
    """
    Celery task for running scientific validation suite.

    Publication-quality hypothesis validation for Nature Digital Medicine:
    - 'reproducibility': Multi-seed reproducibility audit (5 seeds)
    - 'permutation': Placebo control permutation test
    - 'sensitivity': Enhanced sensitivity analysis with data regeneration
    - 'adversarial': Adversarial fidelity check (Turing test)
    - 'null_models': Null model baseline comparison
    - 'subgroups': Subgroup generalization analysis

    Expected runtime: 15-30 minutes for full suite.
    """
    from app import create_app
    from .services.scientific_validation import ScientificValidationService
    app = create_app()
    with app.app_context():
        try:
            total_tasks = len(tasks)
            ProgressTracker.start_job(job_id, total_steps=total_tasks * 100)
            ProgressTracker.update_progress(
                job_id, 2,
                'Starting scientific validation suite...',
                dataset_id=dataset_id,
                tasks=tasks
            )

            def progress_callback(pct, msg):
                ProgressTracker.update_progress(job_id, int(pct), msg)

            results = ScientificValidationService.run_full_validation(
                dataset_id=dataset_id,
                tasks=tasks,
                progress_callback=progress_callback
            )

            ProgressTracker.complete_job(job_id, result={
                'dataset_id': dataset_id,
                'results': results
            })

        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")