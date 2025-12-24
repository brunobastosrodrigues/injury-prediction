import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
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


class TrainingService:
    """Service for training ML models."""

    _model_types = None

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

        model = joblib.load(model_path)

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
        y_test = FileManager.read_df(os.path.join(split_dir, 'y_test')).values.ravel()

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
        from flask import current_app
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            return None

        model = joblib.load(model_path)

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
        y_test = FileManager.read_df(os.path.join(split_dir, 'y_test')).values.ravel()

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