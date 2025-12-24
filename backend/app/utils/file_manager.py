import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from flask import current_app


class FileManager:
    """Manage data files and metadata."""

    @staticmethod
    def get_data_dir() -> str:
        return current_app.config['DATA_DIR']

    @staticmethod
    def get_raw_dir() -> str:
        return current_app.config['RAW_DATA_DIR']

    @staticmethod
    def get_processed_dir() -> str:
        return current_app.config['PROCESSED_DATA_DIR']

    @staticmethod
    def get_models_dir() -> str:
        return current_app.config['MODELS_DIR']

    @classmethod
    def create_dataset_folder(cls, dataset_id: str) -> str:
        """Create a folder for a new dataset."""
        folder_path = os.path.join(cls.get_raw_dir(), dataset_id)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    @classmethod
    def save_dataset_metadata(cls, dataset_id: str, metadata: Dict[str, Any]):
        """Save dataset metadata as JSON."""
        folder_path = os.path.join(cls.get_raw_dir(), dataset_id)
        metadata_path = os.path.join(folder_path, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

    @classmethod
    def get_dataset_metadata(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Load dataset metadata."""
        metadata_path = os.path.join(cls.get_raw_dir(), dataset_id, 'metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None

    @classmethod
    def list_datasets(cls) -> List[Dict[str, Any]]:
        """List all available datasets with their metadata."""
        raw_dir = cls.get_raw_dir()
        datasets = []

        if not os.path.exists(raw_dir):
            return datasets

        for dataset_id in os.listdir(raw_dir):
            dataset_path = os.path.join(raw_dir, dataset_id)
            if os.path.isdir(dataset_path):
                metadata = cls.get_dataset_metadata(dataset_id)
                if metadata:
                    datasets.append({
                        'id': dataset_id,
                        **metadata
                    })
                else:
                    # Basic info if no metadata
                    datasets.append({
                        'id': dataset_id,
                        'created_at': datetime.fromtimestamp(
                            os.path.getctime(dataset_path)
                        ).isoformat()
                    })

        return sorted(datasets, key=lambda x: x.get('created_at', ''), reverse=True)

    @classmethod
    def delete_dataset(cls, dataset_id: str) -> bool:
        """Delete a dataset folder."""
        folder_path = os.path.join(cls.get_raw_dir(), dataset_id)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return True
        return False

    @classmethod
    def get_dataset_summary(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a dataset."""
        folder_path = os.path.join(cls.get_raw_dir(), dataset_id)

        summary = {'id': dataset_id}

        # Load athletes data
        athletes_path = os.path.join(folder_path, 'athletes.csv')
        if os.path.exists(athletes_path):
            df = pd.read_csv(athletes_path)
            summary['n_athletes'] = len(df)
            summary['athlete_columns'] = list(df.columns)

        # Load daily data
        daily_path = os.path.join(folder_path, 'daily_data.csv')
        if os.path.exists(daily_path):
            df = pd.read_csv(daily_path)
            summary['n_daily_records'] = len(df)
            summary['daily_columns'] = list(df.columns)
            summary['injury_rate'] = float(df['injury'].mean()) if 'injury' in df.columns else None
            summary['date_range'] = {
                'start': df['date'].min() if 'date' in df.columns else None,
                'end': df['date'].max() if 'date' in df.columns else None
            }

        # Load activity data
        activity_path = os.path.join(folder_path, 'activity_data.csv')
        if os.path.exists(activity_path):
            df = pd.read_csv(activity_path)
            summary['n_activities'] = len(df)
            summary['activity_columns'] = list(df.columns)
            if 'sport' in df.columns:
                summary['sport_distribution'] = df['sport'].value_counts().to_dict()

        # Load metadata
        metadata = cls.get_dataset_metadata(dataset_id)
        if metadata:
            summary['metadata'] = metadata

        return summary

    @classmethod
    def create_split_folder(cls, split_id: str) -> str:
        """Create a folder for preprocessed split data."""
        folder_path = os.path.join(cls.get_processed_dir(), split_id)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    @classmethod
    def list_splits(cls) -> List[Dict[str, Any]]:
        """List all available preprocessed splits."""
        processed_dir = cls.get_processed_dir()
        splits = []

        if not os.path.exists(processed_dir):
            return splits

        for split_id in os.listdir(processed_dir):
            split_path = os.path.join(processed_dir, split_id)
            if os.path.isdir(split_path):
                metadata_path = os.path.join(split_path, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    splits.append({'id': split_id, **metadata})

        return sorted(splits, key=lambda x: x.get('created_at', ''), reverse=True)

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """List all trained models."""
        models_dir = cls.get_models_dir()
        models = []

        if not os.path.exists(models_dir):
            return models

        for filename in os.listdir(models_dir):
            if filename.endswith('.json'):
                model_id = filename.replace('.json', '')
                metadata_path = os.path.join(models_dir, filename)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                models.append({'id': model_id, **metadata})

        return sorted(models, key=lambda x: x.get('created_at', ''), reverse=True)
