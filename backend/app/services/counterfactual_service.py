import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from flask import current_app

from ..utils.file_manager import FileManager

class CounterfactualService:
    """Service for generating counterfactual explanations."""

    @classmethod
    def _load_model_and_data(cls, model_id: str, split_id: str):
        """Helper to load model and test data."""
        models_dir = current_app.config['MODELS_DIR']
        processed_dir = current_app.config['PROCESSED_DATA_DIR']

        model_path = os.path.join(models_dir, f'{model_id}.joblib')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model {model_id} not found")

        model = joblib.load(model_path)

        # Load test data
        split_dir = os.path.join(processed_dir, split_id)
        try:
            X_test = FileManager.read_df(os.path.join(split_dir, 'X_test'))
            # We also need metadata to map rows back to athletes/dates if the index is lost
            # But usually index is preserved in parquet.
            # Let's check if athlete_id/date are in columns or index.
            # In preprocessing, they might have been dropped or encoded.
            # But we need them to identify the user.
            # Let's assume we can somehow map back.
            # Wait, PreprocessingService._save_split saves X_train/X_test.
            # And _encode_categorical drops athlete_id and date strings.
            # This is a problem. We need to map X_test rows back to athlete/date.

            # We can try to load the original merged df before split? No, that's not saved.
            # But we can try to reconstruct the index if it was preserved.
            pass
        except Exception as e:
             raise FileNotFoundError(f"Data for split {split_id} not found: {str(e)}")

        return model, X_test

    @classmethod
    def get_high_risk_predictions(cls, model_id: str, split_id: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Get high risk predictions from the test set."""
        model, X_test = cls._load_model_and_data(model_id, split_id)

        # Predict
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_test)[:, 1]
        else:
            probs = model.predict(X_test)

        # Filter
        high_risk_indices = np.where(probs > threshold)[0]

        results = []
        # We need to recover athlete_id and date.
        # If they are not in X_test, we are in trouble.
        # Let's inspect X_test columns in a subsequent step.
        # For now, I'll return the index.

        for idx in high_risk_indices:
             results.append({
                 'index': int(idx),
                 'risk': float(probs[idx])
             })

        return results

    @classmethod
    def generate_counterfactuals(cls, model_id: str, split_id: str, instance_index: int) -> Dict[str, Any]:
        """Generate counterfactuals for a specific instance."""
        model, X_test = cls._load_model_and_data(model_id, split_id)

        if instance_index >= len(X_test):
            return None

        instance = X_test.iloc[instance_index].copy()

        # Get baseline risk
        base_risk = model.predict_proba(instance.to_frame().T)[0, 1]

        recommendations = []

        # Define interventions
        # 1. Reduce Training Intensity (actual_tss)
        if 'actual_tss' in instance.index:
            current_tss = instance['actual_tss']
            # Try reducing by 10%, 20%, 30%
            for reduction in [0.1, 0.2, 0.3]:
                modified = instance.copy()
                new_tss = current_tss * (1 - reduction)
                modified['actual_tss'] = new_tss

                # Update derived features
                cls._update_derived_features(modified, 'actual_tss', new_tss - current_tss)

                new_risk = model.predict_proba(modified.to_frame().T)[0, 1]

                if new_risk < base_risk:
                    recommendations.append({
                        'type': 'Reduce Training Intensity',
                        'description': f"Reduce TSS by {int(reduction*100)}% (from {current_tss:.0f} to {new_tss:.0f})",
                        'new_risk': float(new_risk),
                        'risk_reduction': float(base_risk - new_risk)
                    })

        # 2. Improve Sleep (sleep_hours)
        if 'sleep_hours' in instance.index:
            current_sleep = instance['sleep_hours']
            if current_sleep < 9:
                # Try increasing to 8, 9
                for target_sleep in [8, 9]:
                    if target_sleep > current_sleep:
                        modified = instance.copy()
                        modified['sleep_hours'] = target_sleep

                        # Sleep affects recovery? Maybe not explicitly in features but let's see.
                        # Only 'sleep_hours' feature changes.

                        new_risk = model.predict_proba(modified.to_frame().T)[0, 1]

                        if new_risk < base_risk:
                            recommendations.append({
                                'type': 'Increase Sleep',
                                'description': f"Increase sleep to {target_sleep} hours",
                                'new_risk': float(new_risk),
                                'risk_reduction': float(base_risk - new_risk)
                            })

        # Sort by risk reduction
        recommendations.sort(key=lambda x: x['risk_reduction'], reverse=True)

        return {
            'base_risk': float(base_risk),
            'recommendations': recommendations
        }

    @staticmethod
    def _update_derived_features(instance, changed_feature, delta):
        """Update dependent features based on changes."""
        # Simple heuristic updates
        if changed_feature == 'actual_tss':
            # Update TSS based features
            if 'tss_deviation' in instance.index:
                instance['tss_deviation'] += delta

            # ACWR updates (approximation)
            # acute_load (7d sum) changes by delta
            if 'acute_load' in instance.index:
                instance['acute_load'] += delta

            # chronic_load (28d mean * 7) changes by delta / 4
            if 'chronic_load' in instance.index:
                instance['chronic_load'] += delta / 4.0

            # Recalculate ACWR
            if 'acwr' in instance.index and 'chronic_load' in instance.index and instance['chronic_load'] != 0:
                instance['acwr'] = instance['acute_load'] / instance['chronic_load']
