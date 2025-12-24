import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import current_app
from .data_generation_service import DataGenerationService
from ..utils.file_manager import FileManager
from ..utils.progress_tracker import ProgressTracker

class IngestionService:
    """Service for ingesting and processing real-world athlete data."""

    @classmethod
    def ingest_data_async(cls, dataset_id: str, file_path: str, data_type: str = 'garmin') -> str:
        """
        Start async ingestion process.
        Returns job_id.
        """
        from ..celery_app import celery_app
        job_id = ProgressTracker.create_job('data_ingestion')
        
        celery_app.send_task(
            'ingest_real_data',
            args=[job_id, dataset_id, file_path, data_type]
        )
        
        return job_id

    @classmethod
    def process_real_data(cls, file_path: str, data_type: str) -> pd.DataFrame:
        """
        Process uploaded file and map to standard internal format.
        Currently supporting Garmin CSV exports as a proof of concept.
        """
        if data_type == 'garmin_csv':
            df = pd.read_csv(file_path)
            # Map Garmin fields to internal names
            # Synthetic fields: athlete_id, date, resting_hr, hrv, sleep_hours, deep_sleep, 
            # light_sleep, rem_sleep, sleep_quality, body_battery_morning, stress, 
            # body_battery_evening, planned_tss, actual_tss, injury
            
            mapping = {
                'calendarDate': 'date',
                'restingHeartRateInBeatsPerMinute': 'resting_hr',
                'averageStressLevel': 'stress',
                'durationInSeconds': 'sleep_duration_s', # needs conversion
                'overallSleepScore': 'sleep_quality'
            }
            
            # Simple mapping logic
            df = df.rename(columns=mapping)
            
            if 'sleep_duration_s' in df.columns:
                df['sleep_hours'] = df['sleep_duration_s'] / 3600
                
            # Ensure standard fields exist
            required_fields = ['date', 'resting_hr', 'stress', 'sleep_hours', 'sleep_quality']
            for field in required_fields:
                if field not in df.columns:
                    df[field] = np.nan
            
            # Add placeholders for missing synthetic metrics
            df['hrv'] = np.nan
            df['injury'] = df.get('injuryOccured', 0)
            
            return df[required_fields + ['hrv', 'injury']]
        
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    @classmethod
    def merge_real_into_dataset(cls, dataset_id: str, real_df: pd.DataFrame, athlete_id: str):
        """Merge processed real data into an existing dataset."""
        raw_dir = current_app.config['RAW_DATA_DIR']
        dataset_path = os.path.join(raw_dir, dataset_id)
        
        # Load existing daily data
        daily_df = FileManager.read_df(os.path.join(dataset_path, 'daily_data'))
        
        # Mark real data with the athlete_id
        real_df['athlete_id'] = athlete_id
        
        # Append real data
        combined_df = pd.concat([daily_df, real_df], ignore_index=True)
        
        # Save back
        FileManager.save_df(combined_df, os.path.join(dataset_path, 'daily_data.parquet'))
        
        # Update metadata
        metadata = FileManager.get_dataset_metadata(dataset_id)
        if metadata:
            metadata['has_real_data'] = True
            metadata['n_real_records'] = len(real_df)
            FileManager.save_dataset_metadata(dataset_id, metadata)
