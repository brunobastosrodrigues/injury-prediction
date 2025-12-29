import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, confusion_matrix,
    precision_score, recall_score, f1_score, roc_curve, precision_recall_curve
)
import joblib

from ..utils.progress_tracker import ProgressTracker
from ..utils.file_manager import FileManager
from ..celery_app import celery_app

logger = logging.getLogger(__name__)


class TrainingService:
    """Service for training ML models."""

    _model_types = None

    # Allowed model types for validation
    ALLOWED_MODELS = {'xgboost', 'random_forest', 'lasso'}

    # Default hyperparameters for Sim2Real experiments (simplified for transfer learning)
    SIM2REAL_PARAMS = {
        'xgboost': {'n_estimators': 100, 'max_depth': 3, 'learning_rate': 0.1, 'random_state': 42},
        'random_forest': {'n_estimators': 100, 'max_depth': 5, 'random_state': 42},
        'lasso': {'C': 1.0, 'random_state': 42, 'max_iter': 1000}
    }

    @classmethod
    def get_model_types(cls):
        """Load and return model types and hyperparameters from config."""
        if cls._model_types is None:
            from flask import current_app
            import yaml
            # Use current_app.root_path which is /app/app
            config_path = os.path.join(current_app.root_path, 'config', 'hyperparameters.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    cls._model_types = yaml.safe_load(f)
            else:
                # Fallback to empty if file is missing
                cls._model_types = {}
        return cls._model_types

    @classmethod
    def train_sim2real_experiment(
        cls,
        synthetic_df: pd.DataFrame,
        real_df: pd.DataFrame,
        model_type: str = 'xgboost'
    ) -> Dict[str, Any]:
        """
        Experiment B: Train on Synthetic, Test on Real (PMData).

        Trains a model on synthetic data and evaluates zero-shot performance
        on real-world data to assess transfer learning capabilities.

        Args:
            synthetic_df: Synthetic training data with features and target.
            real_df: Real-world test data with same schema.
            model_type: Model to train ('xgboost', 'random_forest', 'lasso').

        Returns:
            Dict containing:
                - auc: ROC AUC score
                - ap: Average precision score
                - n_train: Number of training samples
                - n_test: Number of test samples
                - features_used: List of features used
                - class_distribution: Dict with train/test class distributions

        Raises:
            ValueError: If model_type is invalid, datasets are incompatible,
                       empty, or contain missing values.
            ImportError: If required ML library (e.g., XGBoost) is not installed.
        """
        logger.info(f"Starting Sim2Real experiment with model_type='{model_type}'")

        # Validate model_type
        if model_type not in cls.ALLOWED_MODELS:
            raise ValueError(
                f"Invalid model_type '{model_type}'. Must be one of {cls.ALLOWED_MODELS}"
            )

        # Validate DataFrames are not empty
        if len(synthetic_df) == 0:
            raise ValueError("Synthetic DataFrame is empty")
        if len(real_df) == 0:
            raise ValueError("Real DataFrame is empty")

        # Identify common features dynamically
        potential_features = [
            'sleep_quality_daily', 'stress_score', 'recovery_score',
            'sleep_hours', 'resting_hr'
        ]
        features = [
            f for f in potential_features
            if f in synthetic_df.columns and f in real_df.columns
        ]
        target = 'will_get_injured'

        if not features:
            raise ValueError(
                'No common features found between Synthetic and Real data. '
                f'Expected features: {potential_features}'
            )

        if target not in synthetic_df.columns or target not in real_df.columns:
            raise ValueError(f"Target variable '{target}' missing from one or both datasets")

        logger.info(f"Common features found: {features}")

        # Extract features and target
        X_train = synthetic_df[features]
        y_train = synthetic_df[target]
        X_test = real_df[features]
        y_test = real_df[target]

        # Validate no missing values
        if X_train.isnull().any().any():
            raise ValueError("Synthetic data contains missing values (NaN)")
        if X_test.isnull().any().any():
            raise ValueError("Real data contains missing values (NaN)")

        # Log class distribution and warn about imbalance
        train_pos_rate = y_train.mean()
        test_pos_rate = y_test.mean()
        logger.info(
            f"Training on {len(X_train)} samples (positive rate: {train_pos_rate:.2%}), "
            f"testing on {len(X_test)} samples (positive rate: {test_pos_rate:.2%})"
        )

        if y_train.sum() < 2:
            logger.warning("Very few positive samples in training data - metrics may be unreliable")
        if y_test.sum() < 2:
            logger.warning("Very few positive samples in test data - metrics may be unreliable")

        # Get simplified params for Sim2Real experiment
        params = cls.SIM2REAL_PARAMS.get(model_type, {})
        logger.info(f"Using hyperparameters: {params}")

        # Train model
        model = cls._create_model(model_type, params)
        model.fit(X_train, y_train)
        logger.info("Model training completed")

        # Evaluate on Real Data (Zero-shot transfer)
        probs = model.predict_proba(X_test)[:, 1]

        # Calculate metrics
        auc_score = float(roc_auc_score(y_test, probs))
        ap_score = float(average_precision_score(y_test, probs))

        scores = {
            'auc': auc_score,
            'ap': ap_score,
            'n_train': len(X_train),
            'n_test': len(X_test),
            'features_used': features,
            'class_distribution': {
                'train_positive_rate': float(train_pos_rate),
                'test_positive_rate': float(test_pos_rate)
            }
        }

        logger.info(f"Sim2Real experiment completed - AUC: {auc_score:.3f}, AP: {ap_score:.3f}")
        return scores

    @classmethod
    def train_sim2real_loso(
        cls,
        synthetic_df: pd.DataFrame,
        real_df: pd.DataFrame,
        model_type: str = 'xgboost',
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Leave-One-Subject-Out (LOSO) Cross-Validation for Sim2Real.

        For each of N athletes in real data:
        - Train on synthetic data
        - Test on the held-out athlete

        This provides a more robust estimate of transfer performance
        with proper confidence intervals.

        Args:
            synthetic_df: Synthetic training data with features and target.
            real_df: Real-world data with athlete_id column.
            model_type: Model to train ('xgboost', 'random_forest', 'lasso').
            progress_callback: Optional callback(iteration, total, fold_result) for progress.

        Returns:
            Dict containing:
                - mean_auc: Mean AUC across all folds
                - std_auc: Standard deviation of AUC
                - mean_ap: Mean Average Precision
                - std_ap: Standard deviation of AP
                - fold_results: List of per-fold results
                - n_folds: Number of folds (subjects)
                - confidence_interval_95: (lower, upper) bounds for AUC
        """
        logger.info(f"Starting LOSO Cross-Validation with model_type='{model_type}'")

        # Validate model_type
        if model_type not in cls.ALLOWED_MODELS:
            raise ValueError(f"Invalid model_type '{model_type}'. Must be one of {cls.ALLOWED_MODELS}")

        # Get unique athletes
        if 'athlete_id' not in real_df.columns:
            raise ValueError("Real data must have 'athlete_id' column for LOSO CV")

        athletes = real_df['athlete_id'].unique()
        n_athletes = len(athletes)
        logger.info(f"Found {n_athletes} athletes for LOSO CV")

        if n_athletes < 3:
            raise ValueError(f"Need at least 3 athletes for LOSO CV, found {n_athletes}")

        # Identify common features
        potential_features = [
            'sleep_quality_daily', 'stress_score', 'recovery_score',
            'sleep_hours', 'resting_hr'
        ]
        features = [
            f for f in potential_features
            if f in synthetic_df.columns and f in real_df.columns
        ]
        target = 'will_get_injured'

        if not features:
            raise ValueError('No common features found between Synthetic and Real data')

        if target not in synthetic_df.columns or target not in real_df.columns:
            raise ValueError(f"Target variable '{target}' missing from one or both datasets")

        # Prepare synthetic training data
        X_train_synth = synthetic_df[features].dropna()
        y_train_synth = synthetic_df.loc[X_train_synth.index, target]

        # Run LOSO
        fold_results = []
        for i, test_athlete in enumerate(athletes):
            # Test set: held-out athlete
            test_mask = real_df['athlete_id'] == test_athlete
            X_test = real_df.loc[test_mask, features].dropna()

            if len(X_test) < 5:
                logger.warning(f"Skipping athlete {test_athlete} - only {len(X_test)} samples")
                continue

            y_test = real_df.loc[X_test.index, target]

            # Skip if no positive samples in test set
            if y_test.sum() < 1:
                logger.warning(f"Skipping athlete {test_athlete} - no positive samples")
                continue

            # Train on synthetic data only (pure Sim2Real transfer)
            params = cls.SIM2REAL_PARAMS.get(model_type, {})
            model = cls._create_model(model_type, params)
            model.fit(X_train_synth, y_train_synth)

            # Evaluate on held-out athlete
            try:
                probs = model.predict_proba(X_test)[:, 1]
                auc_score = float(roc_auc_score(y_test, probs))
                ap_score = float(average_precision_score(y_test, probs))
            except Exception as e:
                logger.warning(f"Evaluation failed for athlete {test_athlete}: {e}")
                continue

            fold_result = {
                'fold': i + 1,
                'test_athlete': str(test_athlete),
                'auc': auc_score,
                'ap': ap_score,
                'n_test_samples': len(X_test),
                'test_positive_rate': float(y_test.mean())
            }
            fold_results.append(fold_result)

            if progress_callback:
                progress_callback(i + 1, n_athletes, fold_result)

            logger.info(f"Fold {i+1}/{n_athletes}: Athlete {test_athlete} - AUC={auc_score:.3f}, AP={ap_score:.3f}")

        if len(fold_results) < 3:
            raise ValueError(f"Only {len(fold_results)} valid folds - need at least 3")

        # Calculate statistics
        auc_scores = [r['auc'] for r in fold_results]
        ap_scores = [r['ap'] for r in fold_results]

        mean_auc = float(np.mean(auc_scores))
        std_auc = float(np.std(auc_scores, ddof=1))  # Sample std
        mean_ap = float(np.mean(ap_scores))
        std_ap = float(np.std(ap_scores, ddof=1))

        # 95% confidence interval using t-distribution
        from scipy import stats as scipy_stats
        n = len(auc_scores)
        t_critical = scipy_stats.t.ppf(0.975, n - 1)
        margin = t_critical * (std_auc / np.sqrt(n))
        ci_lower = mean_auc - margin
        ci_upper = mean_auc + margin

        results = {
            'mean_auc': round(mean_auc, 4),
            'std_auc': round(std_auc, 4),
            'mean_ap': round(mean_ap, 4),
            'std_ap': round(std_ap, 4),
            'n_folds': len(fold_results),
            'n_athletes_total': n_athletes,
            'confidence_interval_95': (round(ci_lower, 4), round(ci_upper, 4)),
            'fold_results': fold_results,
            'features_used': features,
            'model_type': model_type,
            # Statistical interpretation
            'interpretation': cls._interpret_loso_results(mean_auc, std_auc, ci_lower, ci_upper)
        }

        logger.info(f"LOSO CV completed: AUC = {mean_auc:.3f} ± {std_auc:.3f} (95% CI: [{ci_lower:.3f}, {ci_upper:.3f}])")
        return results

    @staticmethod
    def _interpret_loso_results(mean_auc, std_auc, ci_lower, ci_upper):
        """Generate scientific interpretation of LOSO results."""
        interpretations = []

        # Mean performance
        if mean_auc >= 0.65:
            interpretations.append("Strong transfer - synthetic data generalizes well to real individuals.")
        elif mean_auc >= 0.60:
            interpretations.append("Good transfer - synthetic data captures key injury patterns.")
        elif mean_auc >= 0.55:
            interpretations.append("Moderate transfer - some signal, but room for improvement.")
        else:
            interpretations.append("Weak transfer - synthetic patterns may not match real data.")

        # Variance interpretation
        if std_auc < 0.05:
            interpretations.append("Low variance indicates stable predictions across individuals.")
        elif std_auc < 0.10:
            interpretations.append("Moderate variance suggests some individual heterogeneity.")
        else:
            interpretations.append("High variance indicates substantial individual differences in predictability.")

        # Confidence interval
        if ci_lower > 0.55:
            interpretations.append("The 95% CI excludes chance level (0.5), supporting statistical significance.")
        elif ci_lower > 0.50:
            interpretations.append("Lower bound above chance, but marginal significance.")
        else:
            interpretations.append("CI includes chance level - results may not be statistically significant.")

        return " ".join(interpretations)

    @classmethod
    def train_async(
        cls,
        split_id: str,
        model_types: List[str],
        hyperparameters: Optional[Dict[str, Dict]] = None
    ) -> str:
        """Start async training and return job_id."""
        job_id = ProgressTracker.create_job('training')

        # Start training using Celery send_task to avoid circular imports
        celery_app.send_task(
            'train_models',
            args=[job_id, split_id, model_types, hyperparameters]
        )

        return job_id

    @classmethod
    def _create_model(cls, model_type: str, params: Dict):
        """Create a model instance."""
        if model_type == 'lasso':
            return LogisticRegression(**params)
        elif model_type == 'random_forest':
            return RandomForestClassifier(**params)
        elif model_type == 'xgboost':
            try:
                from xgboost import XGBClassifier
                # Remove incompatible params
                xgb_params = {k: v for k, v in params.items() if k != 'class_weight'}
                return XGBClassifier(**xgb_params, use_label_encoder=False, eval_metric='logloss')
            except ImportError:
                raise ValueError("XGBoost not installed")
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @classmethod
    def _calculate_metrics(cls, y_true, y_pred, y_pred_proba):
        """Calculate evaluation metrics."""
        return {
            'roc_auc': float(roc_auc_score(y_true, y_pred_proba)),
            'average_precision': float(average_precision_score(y_true, y_pred_proba)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0)),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }

    @classmethod
    def _get_feature_importance(cls, model, feature_names, model_type):
        """Extract feature importance."""
        if model_type == 'lasso':
            importance = np.abs(model.coef_[0])
        elif model_type == 'random_forest':
            importance = model.feature_importances_
        elif model_type == 'xgboost':
            importance = model.feature_importances_
        else:
            return []

        # Sort by importance
        indices = np.argsort(importance)[::-1]
        return [
            {'feature': str(feature_names[i]), 'importance': float(importance[i])}
            for i in indices[:30]  # Top 30
        ]

    @classmethod
    def _save_model(cls, model_id, model, model_type, params, metrics, feature_importance, split_id, feature_names):
        """Save trained model and metadata."""
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        os.makedirs(models_dir, exist_ok=True)

        # Get split/dataset metadata for the registry
        from .preprocessing_service import PreprocessingService
        split_metadata = PreprocessingService.get_split(split_id)
        dataset_id = split_metadata.get('dataset_id') if split_metadata else 'unknown'

        # Save model
        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        joblib.dump(model, model_path)

        # Save metadata (Model Registry Entry)
        metadata = {
            'model_id': model_id,
            'model_type': model_type,
            'model_name': cls.get_model_types().get(model_type, {}).get('name', model_type),
            'hyperparameters': params,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'split_id': split_id,
            'dataset_id': dataset_id,
            'feature_names': feature_names,
            'created_at': datetime.utcnow().isoformat(),
            'split_details': {
                'strategy': split_metadata.get('split_strategy'),
                'ratio': split_metadata.get('split_ratio'),
                'train_samples': split_metadata.get('train_samples')
            } if split_metadata else {}
        }

        metadata_path = os.path.join(models_dir, f'{model_id}.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def get_training_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job status."""
        return ProgressTracker.get_job(job_id)

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """List all trained models."""
        return FileManager.list_models()

    @classmethod
    def get_model(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model details."""
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None

    @classmethod
    def get_roc_curve(cls, model_id: str, split_id: str) -> Optional[Dict[str, Any]]:
        """Get ROC curve data for a model."""
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            return None

        try:
            model = joblib.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            return None

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        try:
            X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
            y_test = FileManager.read_df(os.path.join(split_dir, 'y_test')).values.ravel()
        except Exception as e:
            logger.error(f"Failed to load test data from {split_dir}: {e}")
            return None

        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
        except Exception as e:
            logger.error(f"Failed to compute ROC curve: {e}")
            return None

        return {
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'thresholds': thresholds.tolist(),
            'auc': float(roc_auc_score(y_test, y_pred_proba))
        }

    @classmethod
    def get_pr_curve(cls, model_id: str, split_id: str) -> Optional[Dict[str, Any]]:
        """Get Precision-Recall curve data for a model."""
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            return None

        try:
            model = joblib.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            return None

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        try:
            X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
            y_test = FileManager.read_df(os.path.join(split_dir, 'y_test')).values.ravel()
        except Exception as e:
            logger.error(f"Failed to load test data from {split_dir}: {e}")
            return None

        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
        except Exception as e:
            logger.error(f"Failed to compute PR curve: {e}")
            return None

        return {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist(),
            'average_precision': float(average_precision_score(y_test, y_pred_proba))
        }

    @classmethod
    def compare_models(cls, model_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple models."""
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        comparison = []

        for model_id in model_ids:
            metadata_path = os.path.join(models_dir, f'{model_id}.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    comparison.append({
                        'model_id': model_id,
                        'model_type': metadata.get('model_type'),
                        'model_name': metadata.get('model_name'),
                        'dataset_id': metadata.get('dataset_id'),
                        'split_id': metadata.get('split_id'),
                        'metrics': metadata.get('metrics'),
                        'created_at': metadata.get('created_at')
                    })

        return {'models': comparison}