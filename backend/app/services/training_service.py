import os
import json
import uuid
import threading
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from flask import current_app
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, confusion_matrix,
    precision_score, recall_score, f1_score, roc_curve, precision_recall_curve
)
import joblib

from ..utils.progress_tracker import ProgressTracker
from ..utils.file_manager import FileManager


class TrainingService:
    """Service for training ML models."""

    MODEL_TYPES = {
        'lasso': {
            'name': 'LASSO Logistic Regression',
            'default_params': {
                'penalty': 'l1',
                'solver': 'saga',
                'max_iter': 1000,
                'class_weight': 'balanced',
                'random_state': 42
            }
        },
        'random_forest': {
            'name': 'Random Forest',
            'default_params': {
                'n_estimators': 200,
                'max_depth': 8,
                'min_samples_leaf': 7,
                'class_weight': 'balanced',
                'random_state': 42,
                'n_jobs': -1
            }
        },
        'xgboost': {
            'name': 'XGBoost',
            'default_params': {
                'n_estimators': 400,
                'max_depth': 2,
                'learning_rate': 0.03,
                'subsample': 0.8,
                'colsample_bytree': 0.7,
                'reg_alpha': 1.0,
                'reg_lambda': 2.0,
                'random_state': 42,
                'n_jobs': -1
            }
        }
    }

    @classmethod
    def train_async(
        cls,
        split_id: str,
        model_types: List[str],
        hyperparameters: Optional[Dict[str, Dict]] = None
    ) -> str:
        """Start async training and return job_id."""
        job_id = ProgressTracker.create_job('training')

        thread = threading.Thread(
            target=cls._run_training,
            args=(job_id, split_id, model_types, hyperparameters),
            daemon=True
        )
        thread.start()

        return job_id

    @classmethod
    def _run_training(
        cls,
        job_id: str,
        split_id: str,
        model_types: List[str],
        hyperparameters: Optional[Dict[str, Dict]]
    ):
        """Run the actual training."""
        try:
            from app import create_app
            app = create_app()

            with app.app_context():
                total_steps = len(model_types) * 2  # training + evaluation per model
                ProgressTracker.start_job(job_id, total_steps=total_steps)

                # Load data
                ProgressTracker.update_progress(job_id, 5, 'Loading data...')
                processed_dir = current_app.config['PROCESSED_DATA_DIR']
                split_dir = os.path.join(processed_dir, split_id)

                X_train = pd.read_csv(os.path.join(split_dir, 'X_train.csv'))
                X_test = pd.read_csv(os.path.join(split_dir, 'X_test.csv'))
                y_train = pd.read_csv(os.path.join(split_dir, 'y_train.csv')).values.ravel()
                y_test = pd.read_csv(os.path.join(split_dir, 'y_test.csv')).values.ravel()

                trained_models = []

                for i, model_type in enumerate(model_types):
                    step = (i + 1) / len(model_types) * 80 + 10
                    ProgressTracker.update_progress(
                        job_id, int(step),
                        f'Training {cls.MODEL_TYPES.get(model_type, {}).get("name", model_type)}...'
                    )

                    # Get hyperparameters
                    params = cls.MODEL_TYPES.get(model_type, {}).get('default_params', {}).copy()
                    if hyperparameters and model_type in hyperparameters:
                        params.update(hyperparameters[model_type])

                    # Train model
                    model = cls._create_model(model_type, params)
                    model.fit(X_train, y_train)

                    # Evaluate
                    y_pred = model.predict(X_test)
                    y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred

                    metrics = cls._calculate_metrics(y_test, y_pred, y_pred_proba)

                    # Get feature importance
                    feature_importance = cls._get_feature_importance(model, X_train.columns, model_type)

                    # Save model
                    model_id = f"model_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
                    cls._save_model(model_id, model, model_type, params, metrics, feature_importance, split_id, X_test.columns.tolist())

                    trained_models.append({
                        'model_id': model_id,
                        'model_type': model_type,
                        'metrics': metrics
                    })

                ProgressTracker.complete_job(job_id, result={'models': trained_models})

        except Exception as e:
            import traceback
            ProgressTracker.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")

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
        models_dir = current_app.config['MODELS_DIR']
        os.makedirs(models_dir, exist_ok=True)

        # Save model
        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        joblib.dump(model, model_path)

        # Save metadata
        metadata = {
            'model_type': model_type,
            'model_name': cls.MODEL_TYPES.get(model_type, {}).get('name', model_type),
            'hyperparameters': params,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'split_id': split_id,
            'feature_names': feature_names,
            'created_at': datetime.utcnow().isoformat()
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
        models_dir = current_app.config['MODELS_DIR']
        metadata_path = os.path.join(models_dir, f'{model_id}.json')

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None

    @classmethod
    def get_roc_curve(cls, model_id: str, split_id: str) -> Optional[Dict[str, Any]]:
        """Get ROC curve data for a model."""
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            return None

        model = joblib.load(model_path)

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        X_test = pd.read_csv(os.path.join(split_dir, 'X_test.csv'))
        y_test = pd.read_csv(os.path.join(split_dir, 'y_test.csv')).values.ravel()

        y_pred_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

        return {
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'thresholds': thresholds.tolist(),
            'auc': float(roc_auc_score(y_test, y_pred_proba))
        }

    @classmethod
    def get_pr_curve(cls, model_id: str, split_id: str) -> Optional[Dict[str, Any]]:
        """Get Precision-Recall curve data for a model."""
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            return None

        model = joblib.load(model_path)

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        X_test = pd.read_csv(os.path.join(split_dir, 'X_test.csv'))
        y_test = pd.read_csv(os.path.join(split_dir, 'y_test.csv')).values.ravel()

        y_pred_proba = model.predict_proba(X_test)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)

        return {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist(),
            'average_precision': float(average_precision_score(y_test, y_pred_proba))
        }

    @classmethod
    def compare_models(cls, model_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple models."""
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
                        'metrics': metadata.get('metrics'),
                        'created_at': metadata.get('created_at')
                    })

        return {'models': comparison}
