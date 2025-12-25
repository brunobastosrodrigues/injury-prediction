"""
Explainability Service - SHAP and Counterfactual Analysis

This module implements model interpretability features for Federated Learning:
1. Local SHAP explanations (computed client-side)
2. Global SHAP aggregation (privacy-preserving)
3. Interaction analysis (SHAP dependence)
4. Counterfactual generation (actionable recommendations)

Key Design Principles:
- Privacy-First: All raw data explanations stay on client (athlete's device)
- Federated XAI: Only aggregated SHAP values sent to server
- Actionable: Provides "what-if" scenarios, not just "why"
"""

import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Tuple, Optional, Any
import json
from pathlib import Path

# SHAP for interpretability
import shap

# Dice-ML for counterfactuals
import dice_ml

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExplainabilityService:
    """
    Service for generating model explanations using SHAP and counterfactuals.

    Designed for Federated Learning:
    - Local explanations computed on client device
    - Global insights aggregated on server
    """

    def __init__(self, model_path: str, dataset_id: str, model_type: str = "xgboost"):
        """
        Initialize explainability service.

        Args:
            model_path: Path to trained model file
            dataset_id: Dataset identifier
            model_type: Type of model (xgboost, random_forest, lasso)
        """
        self.model_path = Path(model_path)
        self.dataset_id = dataset_id
        self.model_type = model_type
        self.model = None
        self.explainer = None
        self.feature_names = None

        # Load model
        self._load_model()

    def _load_model(self):
        """Load the trained model and initialize SHAP explainer."""
        try:
            logger.info(f"Loading model from {self.model_path}")

            if self.model_type in ["xgboost", "random_forest"]:
                self.model = joblib.load(self.model_path)

                # For tree-based models, use TreeExplainer (fast and exact)
                logger.info("Initializing SHAP TreeExplainer")
                self.explainer = shap.TreeExplainer(
                    self.model,
                    feature_perturbation="interventional"  # Better for correlated features
                )
            elif self.model_type == "lasso":
                self.model = joblib.load(self.model_path)

                # For linear models, use LinearExplainer
                logger.info("Initializing SHAP LinearExplainer")
                # Note: LinearExplainer requires background data
                # Will be set when calling explain methods
                self.explainer = None  # Will be created with background data
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")

            logger.info("Model and explainer loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def explain_prediction(
        self,
        X: pd.DataFrame,
        prediction_index: int = -1,
        max_display: int = 10
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a single prediction (Waterfall plot data).

        This is the LOCAL explanation - "Why am I at risk TODAY?"
        Stays on the athlete's device in FL setting.

        Args:
            X: Feature data (single row or multiple rows)
            prediction_index: Index of prediction to explain (-1 = most recent)
            max_display: Maximum number of features to display

        Returns:
            Dict containing:
            - base_value: Model's base prediction
            - shap_values: SHAP values for each feature
            - feature_values: Actual feature values
            - feature_names: Feature names
            - prediction: Model's prediction
        """
        try:
            logger.info(f"Generating SHAP explanation for prediction {prediction_index}")

            # Ensure X is DataFrame
            if not isinstance(X, pd.DataFrame):
                raise ValueError("X must be a pandas DataFrame")

            # Store feature names
            self.feature_names = X.columns.tolist()

            # Get SHAP values
            if self.model_type == "lasso":
                # For linear models, create explainer with background data
                explainer = shap.LinearExplainer(self.model, X)
                shap_values = explainer(X)
            else:
                shap_values = self.explainer(X)

            # Get specific prediction
            if prediction_index == -1:
                prediction_index = len(X) - 1

            # Extract values for single prediction
            single_shap = shap_values[prediction_index]

            # Get model prediction
            if hasattr(self.model, 'predict_proba'):
                prediction = self.model.predict_proba(X.iloc[[prediction_index]])[:, 1][0]
            else:
                prediction = self.model.predict(X.iloc[[prediction_index]])[0]

            # Sort features by absolute SHAP value
            shap_vals = single_shap.values
            feature_vals = X.iloc[prediction_index].values

            # Create sorted indices
            sorted_indices = np.argsort(np.abs(shap_vals))[::-1][:max_display]

            return {
                "base_value": float(single_shap.base_values),
                "shap_values": shap_vals[sorted_indices].tolist(),
                "feature_values": feature_vals[sorted_indices].tolist(),
                "feature_names": [self.feature_names[i] for i in sorted_indices],
                "prediction": float(prediction),
                "prediction_index": prediction_index,
                "explanation_type": "waterfall"
            }

        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {str(e)}")
            raise

    def explain_interactions(
        self,
        X: pd.DataFrame,
        feature1: str,
        feature2: Optional[str] = None,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate SHAP dependence plot data for interaction analysis.

        This reveals the "Training-Injury Prevention Paradox":
        - High load OK if stress is low
        - High load RISKY if stress is high

        Args:
            X: Feature data
            feature1: Primary feature to analyze (e.g., "Acute_TSS")
            feature2: Interaction feature (e.g., "Daily_Stress").
                     If None, auto-detected by SHAP
            sample_size: Number of samples to use (for performance)

        Returns:
            Dict containing:
            - feature1_values: Values of primary feature
            - shap_values: SHAP values for primary feature
            - interaction_values: Values of interaction feature (color coding)
            - feature1_name: Name of primary feature
            - feature2_name: Name of interaction feature
        """
        try:
            logger.info(f"Generating interaction analysis for {feature1}")

            # Sample data if too large
            if len(X) > sample_size:
                X_sample = X.sample(n=sample_size, random_state=42)
            else:
                X_sample = X

            # Get SHAP values
            if self.model_type == "lasso":
                explainer = shap.LinearExplainer(self.model, X_sample)
                shap_values = explainer(X_sample)
            else:
                shap_values = self.explainer(X_sample)

            # Get feature index
            feature_idx = list(X.columns).index(feature1)

            # Auto-detect interaction feature if not specified
            if feature2 is None:
                # SHAP can auto-detect the strongest interaction
                interaction_idx = shap.approximate_interactions(
                    feature_idx,
                    shap_values.values,
                    X_sample.values
                )[0]
                feature2 = X.columns[interaction_idx]

            interaction_idx = list(X.columns).index(feature2)

            return {
                "feature1_values": X_sample[feature1].values.tolist(),
                "shap_values": shap_values.values[:, feature_idx].tolist(),
                "interaction_values": X_sample[feature2].values.tolist(),
                "feature1_name": feature1,
                "feature2_name": feature2,
                "explanation_type": "dependence"
            }

        except Exception as e:
            logger.error(f"Error generating interaction analysis: {str(e)}")
            raise

    def compute_global_shap(
        self,
        X: pd.DataFrame,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Compute global SHAP values (Beeswarm plot data).

        In Federated Learning:
        - Each client computes this locally
        - Only AVERAGE feature impacts sent to server
        - Builds global understanding without sharing raw data

        Args:
            X: Feature data
            sample_size: Number of samples to use

        Returns:
            Dict containing:
            - mean_shap_values: Average SHAP value per feature (privacy-safe)
            - feature_names: Feature names
            - shap_values_distribution: For visualization (optional, client-only)
        """
        try:
            logger.info("Computing global SHAP values")

            # Sample data if too large
            if len(X) > sample_size:
                X_sample = X.sample(n=sample_size, random_state=42)
            else:
                X_sample = X

            # Get SHAP values
            if self.model_type == "lasso":
                explainer = shap.LinearExplainer(self.model, X_sample)
                shap_values = explainer(X_sample)
            else:
                shap_values = self.explainer(X_sample)

            # Compute mean absolute SHAP values (privacy-preserving aggregation)
            mean_shap = np.abs(shap_values.values).mean(axis=0)

            # Sort by importance
            sorted_indices = np.argsort(mean_shap)[::-1]

            return {
                "mean_shap_values": mean_shap[sorted_indices].tolist(),
                "feature_names": [X.columns[i] for i in sorted_indices],
                "explanation_type": "global",
                # Optional: full distribution for client-side visualization
                "shap_values_matrix": shap_values.values.tolist(),
                "feature_values_matrix": X_sample.values.tolist()
            }

        except Exception as e:
            logger.error(f"Error computing global SHAP: {str(e)}")
            raise

    def generate_counterfactuals(
        self,
        X_query: pd.DataFrame,
        desired_class: int = 0,
        total_cfs: int = 3,
        continuous_features: Optional[List[str]] = None,
        immutable_features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate counterfactual explanations (actionable recommendations).

        "What should I change to avoid injury?"

        Args:
            X_query: Current athlete state (high risk)
            desired_class: Desired outcome (0 = no injury, 1 = injury)
            total_cfs: Number of counterfactual scenarios to generate
            continuous_features: List of continuous feature names
            immutable_features: Features that cannot be changed (e.g., Age, Gender)

        Returns:
            Dict containing counterfactual scenarios with recommendations
        """
        try:
            logger.info("Generating counterfactual explanations")

            # Load training data for dice-ml (needed for feasibility constraints)
            data_dir = Path("data/processed") / self.dataset_id
            train_data = pd.read_csv(data_dir / "X_train.csv")

            # Combine with target (needed for dice-ml interface)
            y_train = pd.read_csv(data_dir / "y_train.csv")
            train_data['Injury_7day'] = y_train['Injury_7day']

            # Auto-detect feature types if not specified
            if continuous_features is None:
                continuous_features = X_query.select_dtypes(
                    include=['float64', 'int64']
                ).columns.tolist()

            # Default immutable features (athlete characteristics)
            if immutable_features is None:
                immutable_features = ['Age', 'Gender', 'Years_Experience']
                # Filter to only existing features
                immutable_features = [f for f in immutable_features if f in X_query.columns]

            # Create dice-ml data interface
            d = dice_ml.Data(
                dataframe=train_data,
                continuous_features=continuous_features,
                outcome_name='Injury_7day'
            )

            # Create dice-ml model interface
            m = dice_ml.Model(model=self.model, backend='sklearn')

            # Create DiCE explainer
            exp = dice_ml.Dice(d, m, method='random')

            # Generate counterfactuals
            query_instance = X_query.iloc[0:1]  # Single instance

            dice_exp = exp.generate_counterfactuals(
                query_instance,
                total_CFs=total_cfs,
                desired_class=desired_class,
                features_to_vary=[f for f in continuous_features if f not in immutable_features]
            )

            # Extract counterfactuals
            cf_df = dice_exp.cf_examples_list[0].final_cfs_df

            if cf_df is None or len(cf_df) == 0:
                logger.warning("No counterfactuals found")
                return {
                    "counterfactuals": [],
                    "original_prediction": None,
                    "explanation_type": "counterfactual"
                }

            # Get original prediction
            if hasattr(self.model, 'predict_proba'):
                original_pred = self.model.predict_proba(query_instance)[:, 1][0]
            else:
                original_pred = self.model.predict(query_instance)[0]

            # Format counterfactuals as actionable recommendations
            counterfactuals = []
            for idx, cf_row in cf_df.iterrows():
                # Compute differences from original
                changes = {}
                for col in X_query.columns:
                    original_val = query_instance[col].values[0]
                    cf_val = cf_row[col]

                    if col not in immutable_features:
                        diff = cf_val - original_val
                        if abs(diff) > 1e-6:  # Only report meaningful changes
                            changes[col] = {
                                "from": float(original_val),
                                "to": float(cf_val),
                                "change": float(diff)
                            }

                # Get new prediction
                cf_features = cf_row.drop('Injury_7day').to_frame().T
                if hasattr(self.model, 'predict_proba'):
                    cf_pred = self.model.predict_proba(cf_features)[:, 1][0]
                else:
                    cf_pred = self.model.predict(cf_features)[0]

                counterfactuals.append({
                    "changes": changes,
                    "predicted_risk": float(cf_pred),
                    "risk_reduction": float(original_pred - cf_pred)
                })

            return {
                "counterfactuals": counterfactuals,
                "original_prediction": float(original_pred),
                "explanation_type": "counterfactual",
                "total_scenarios": len(counterfactuals)
            }

        except Exception as e:
            logger.error(f"Error generating counterfactuals: {str(e)}")
            raise

    def generate_recommendations(
        self,
        X_query: pd.DataFrame,
        risk_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on SHAP + Counterfactuals.

        Combines:
        1. SHAP: "What's driving your risk?"
        2. Counterfactuals: "What should you change?"

        Args:
            X_query: Current athlete state
            risk_threshold: Risk threshold for triggering recommendations

        Returns:
            Dict containing prioritized recommendations
        """
        try:
            logger.info("Generating actionable recommendations")

            # Get current risk
            if hasattr(self.model, 'predict_proba'):
                current_risk = self.model.predict_proba(X_query)[:, 1][0]
            else:
                current_risk = self.model.predict(X_query)[0]

            recommendations = {
                "current_risk": float(current_risk),
                "risk_level": "high" if current_risk >= risk_threshold else "low",
                "actions": []
            }

            if current_risk < risk_threshold:
                recommendations["message"] = "Your current injury risk is low. Maintain current habits."
                return recommendations

            # Get SHAP explanation to identify risk drivers
            shap_exp = self.explain_prediction(X_query, prediction_index=0)

            # Get counterfactuals for actionable changes
            cf_exp = self.generate_counterfactuals(X_query, desired_class=0, total_cfs=3)

            # Prioritize recommendations based on:
            # 1. SHAP importance (what matters most)
            # 2. Counterfactual feasibility (what's changeable)

            # Extract top risk factors from SHAP
            top_risk_factors = []
            for i, (feat, shap_val) in enumerate(zip(shap_exp['feature_names'], shap_exp['shap_values'])):
                if shap_val > 0:  # Positive SHAP = increases risk
                    top_risk_factors.append({
                        "feature": feat,
                        "impact": float(shap_val),
                        "current_value": float(shap_exp['feature_values'][i])
                    })

            # Sort by impact
            top_risk_factors = sorted(top_risk_factors, key=lambda x: x['impact'], reverse=True)[:5]

            # Match with counterfactual changes
            if cf_exp['counterfactuals']:
                best_cf = cf_exp['counterfactuals'][0]  # Highest risk reduction

                for factor in top_risk_factors:
                    feat = factor['feature']
                    if feat in best_cf['changes']:
                        change = best_cf['changes'][feat]

                        # Generate human-readable recommendation
                        direction = "increase" if change['change'] > 0 else "decrease"
                        magnitude = abs(change['change'])

                        recommendations["actions"].append({
                            "feature": feat,
                            "current_value": change['from'],
                            "recommended_value": change['to'],
                            "action": f"{direction.capitalize()} {feat.replace('_', ' ')} by {magnitude:.1f}",
                            "impact": factor['impact'],
                            "expected_risk_reduction": best_cf['risk_reduction']
                        })

            if not recommendations["actions"]:
                recommendations["message"] = "Risk is elevated, but no simple interventions identified. Consult a coach."
            else:
                recommendations["message"] = f"Found {len(recommendations['actions'])} actionable recommendations to reduce risk."

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise


def explain_model_globally(dataset_id: str, model_name: str = "xgboost") -> Dict[str, Any]:
    """
    Convenience function to generate global model explanation.

    Args:
        dataset_id: Dataset identifier
        model_name: Model name (xgboost, random_forest, lasso)

    Returns:
        Global SHAP explanation
    """
    # Load model
    model_dir = Path("data/models") / dataset_id
    model_path = model_dir / f"{model_name}_model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load test data
    data_dir = Path("data/processed") / dataset_id
    X_test = pd.read_csv(data_dir / "X_test.csv")

    # Create explainer
    explainer = ExplainabilityService(
        model_path=str(model_path),
        dataset_id=dataset_id,
        model_type=model_name
    )

    # Generate global explanation
    return explainer.compute_global_shap(X_test)


def explain_athlete_risk(
    dataset_id: str,
    athlete_id: int,
    model_name: str = "xgboost",
    date_index: int = -1
) -> Dict[str, Any]:
    """
    Convenience function to explain a specific athlete's risk on a specific day.

    Args:
        dataset_id: Dataset identifier
        athlete_id: Athlete ID
        model_name: Model name
        date_index: Index of date to explain (-1 = most recent)

    Returns:
        Local SHAP explanation + recommendations
    """
    # Load model
    model_dir = Path("data/models") / dataset_id
    model_path = model_dir / f"{model_name}_model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load test data
    data_dir = Path("data/processed") / dataset_id
    X_test = pd.read_csv(data_dir / "X_test.csv")

    # Filter to athlete
    # Assuming there's an Athlete_ID column or similar
    # Adjust based on your actual data structure
    athlete_data = X_test  # Placeholder - filter by athlete_id

    if len(athlete_data) == 0:
        raise ValueError(f"No data found for athlete {athlete_id}")

    # Create explainer
    explainer = ExplainabilityService(
        model_path=str(model_path),
        dataset_id=dataset_id,
        model_type=model_name
    )

    # Generate explanation
    explanation = explainer.explain_prediction(athlete_data, prediction_index=date_index)

    # Generate recommendations
    query_data = athlete_data.iloc[[date_index if date_index != -1 else -1]]
    recommendations = explainer.generate_recommendations(query_data)

    return {
        "explanation": explanation,
        "recommendations": recommendations
    }
