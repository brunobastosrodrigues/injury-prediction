"""
Explainability API Routes

Endpoints for model interpretability:
- SHAP explanations (local and global)
- Interaction analysis
- Counterfactual generation
- Actionable recommendations
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import pandas as pd

from app.services.explainability import (
    ExplainabilityService,
    explain_model_globally,
    explain_athlete_risk
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

explainability_bp = Blueprint('explainability', __name__, url_prefix='/api/explainability')


@explainability_bp.route('/explain/prediction', methods=['POST'])
def explain_prediction():
    """
    Generate SHAP explanation for a single prediction (Waterfall plot).

    Request Body:
    {
        "dataset_id": "dataset_123",
        "model_name": "xgboost",
        "athlete_data": {...},  # Feature values for athlete
        "prediction_index": -1,  # -1 = most recent
        "max_display": 10
    }

    Response:
    {
        "base_value": 0.15,
        "shap_values": [0.05, -0.03, ...],
        "feature_values": [7.5, 85, ...],
        "feature_names": ["Sleep_Hours", "Resting_HR", ...],
        "prediction": 0.42,
        "explanation_type": "waterfall"
    }
    """
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        model_name = data.get('model_name', 'xgboost')
        athlete_data = data.get('athlete_data')
        prediction_index = data.get('prediction_index', -1)
        max_display = data.get('max_display', 10)

        # Validate inputs
        if not dataset_id:
            return jsonify({"error": "dataset_id is required"}), 400

        if not athlete_data:
            return jsonify({"error": "athlete_data is required"}), 400

        # Load model
        model_dir = Path("data/models") / dataset_id
        model_path = model_dir / f"{model_name}_model.pkl"

        if not model_path.exists():
            return jsonify({"error": f"Model not found: {model_name}"}), 404

        # Convert athlete_data to DataFrame
        X = pd.DataFrame([athlete_data]) if isinstance(athlete_data, dict) else pd.DataFrame(athlete_data)

        # Create explainer
        explainer = ExplainabilityService(
            model_path=str(model_path),
            dataset_id=dataset_id,
            model_type=model_name
        )

        # Generate explanation
        explanation = explainer.explain_prediction(
            X,
            prediction_index=prediction_index,
            max_display=max_display
        )

        return jsonify(explanation), 200

    except Exception as e:
        logger.error(f"Error in explain_prediction: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/explain/global', methods=['POST'])
def explain_global():
    """
    Generate global SHAP explanation (Beeswarm plot).

    Request Body:
    {
        "dataset_id": "dataset_123",
        "model_name": "xgboost",
        "sample_size": 1000
    }

    Response:
    {
        "mean_shap_values": [0.15, 0.12, ...],
        "feature_names": ["Acute_TSS", "Sleep_Hours", ...],
        "explanation_type": "global"
    }
    """
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        model_name = data.get('model_name', 'xgboost')
        sample_size = data.get('sample_size', 1000)

        # Validate inputs
        if not dataset_id:
            return jsonify({"error": "dataset_id is required"}), 400

        # Load model
        model_dir = Path("data/models") / dataset_id
        model_path = model_dir / f"{model_name}_model.pkl"

        if not model_path.exists():
            return jsonify({"error": f"Model not found: {model_name}"}), 404

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
        explanation = explainer.compute_global_shap(X_test, sample_size=sample_size)

        return jsonify(explanation), 200

    except Exception as e:
        logger.error(f"Error in explain_global: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/explain/interactions', methods=['POST'])
def explain_interactions():
    """
    Generate SHAP dependence plot for interaction analysis.

    Request Body:
    {
        "dataset_id": "dataset_123",
        "model_name": "xgboost",
        "feature1": "Acute_TSS",
        "feature2": "Daily_Stress",  # Optional, auto-detected if null
        "sample_size": 1000
    }

    Response:
    {
        "feature1_values": [100, 150, ...],
        "shap_values": [0.05, 0.12, ...],
        "interaction_values": [3, 7, ...],
        "feature1_name": "Acute_TSS",
        "feature2_name": "Daily_Stress",
        "explanation_type": "dependence"
    }
    """
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        model_name = data.get('model_name', 'xgboost')
        feature1 = data.get('feature1')
        feature2 = data.get('feature2')
        sample_size = data.get('sample_size', 1000)

        # Validate inputs
        if not dataset_id or not feature1:
            return jsonify({"error": "dataset_id and feature1 are required"}), 400

        # Load model
        model_dir = Path("data/models") / dataset_id
        model_path = model_dir / f"{model_name}_model.pkl"

        if not model_path.exists():
            return jsonify({"error": f"Model not found: {model_name}"}), 404

        # Load test data
        data_dir = Path("data/processed") / dataset_id
        X_test = pd.read_csv(data_dir / "X_test.csv")

        # Create explainer
        explainer = ExplainabilityService(
            model_path=str(model_path),
            dataset_id=dataset_id,
            model_type=model_name
        )

        # Generate interaction explanation
        explanation = explainer.explain_interactions(
            X_test,
            feature1=feature1,
            feature2=feature2,
            sample_size=sample_size
        )

        return jsonify(explanation), 200

    except Exception as e:
        logger.error(f"Error in explain_interactions: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/counterfactuals', methods=['POST'])
def generate_counterfactuals():
    """
    Generate counterfactual explanations (What-If scenarios).

    Request Body:
    {
        "dataset_id": "dataset_123",
        "model_name": "xgboost",
        "athlete_data": {...},
        "desired_class": 0,
        "total_cfs": 3,
        "continuous_features": ["Sleep_Hours", "Acute_TSS", ...],
        "immutable_features": ["Age", "Gender"]
    }

    Response:
    {
        "counterfactuals": [
            {
                "changes": {
                    "Sleep_Hours": {"from": 6, "to": 8, "change": 2},
                    "Acute_TSS": {"from": 150, "to": 120, "change": -30}
                },
                "predicted_risk": 0.15,
                "risk_reduction": 0.27
            }
        ],
        "original_prediction": 0.42,
        "total_scenarios": 3
    }
    """
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        model_name = data.get('model_name', 'xgboost')
        athlete_data = data.get('athlete_data')
        desired_class = data.get('desired_class', 0)
        total_cfs = data.get('total_cfs', 3)
        continuous_features = data.get('continuous_features')
        immutable_features = data.get('immutable_features')

        # Validate inputs
        if not dataset_id or not athlete_data:
            return jsonify({"error": "dataset_id and athlete_data are required"}), 400

        # Load model
        model_dir = Path("data/models") / dataset_id
        model_path = model_dir / f"{model_name}_model.pkl"

        if not model_path.exists():
            return jsonify({"error": f"Model not found: {model_name}"}), 404

        # Convert athlete_data to DataFrame
        X = pd.DataFrame([athlete_data]) if isinstance(athlete_data, dict) else pd.DataFrame(athlete_data)

        # Create explainer
        explainer = ExplainabilityService(
            model_path=str(model_path),
            dataset_id=dataset_id,
            model_type=model_name
        )

        # Generate counterfactuals
        explanation = explainer.generate_counterfactuals(
            X,
            desired_class=desired_class,
            total_cfs=total_cfs,
            continuous_features=continuous_features,
            immutable_features=immutable_features
        )

        return jsonify(explanation), 200

    except Exception as e:
        logger.error(f"Error in generate_counterfactuals: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """
    Generate actionable recommendations based on SHAP + Counterfactuals.

    Request Body:
    {
        "dataset_id": "dataset_123",
        "model_name": "xgboost",
        "athlete_data": {...},
        "risk_threshold": 0.3
    }

    Response:
    {
        "current_risk": 0.42,
        "risk_level": "high",
        "message": "Found 3 actionable recommendations to reduce risk.",
        "actions": [
            {
                "feature": "Sleep_Hours",
                "current_value": 6,
                "recommended_value": 8,
                "action": "Increase Sleep Hours by 2.0",
                "impact": 0.15,
                "expected_risk_reduction": 0.27
            }
        ]
    }
    """
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        model_name = data.get('model_name', 'xgboost')
        athlete_data = data.get('athlete_data')
        risk_threshold = data.get('risk_threshold', 0.3)

        # Validate inputs
        if not dataset_id or not athlete_data:
            return jsonify({"error": "dataset_id and athlete_data are required"}), 400

        # Load model
        model_dir = Path("data/models") / dataset_id
        model_path = model_dir / f"{model_name}_model.pkl"

        if not model_path.exists():
            return jsonify({"error": f"Model not found: {model_name}"}), 404

        # Convert athlete_data to DataFrame
        X = pd.DataFrame([athlete_data]) if isinstance(athlete_data, dict) else pd.DataFrame(athlete_data)

        # Create explainer
        explainer = ExplainabilityService(
            model_path=str(model_path),
            dataset_id=dataset_id,
            model_type=model_name
        )

        # Generate recommendations
        recommendations = explainer.generate_recommendations(
            X,
            risk_threshold=risk_threshold
        )

        return jsonify(recommendations), 200

    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/athlete/<dataset_id>/<int:athlete_id>', methods=['GET'])
def get_athlete_explanation(dataset_id: str, athlete_id: int):
    """
    Get comprehensive explanation for a specific athlete.

    Query Parameters:
    - model_name: Model to use (default: xgboost)
    - date_index: Index of date to explain (default: -1, most recent)

    Response:
    {
        "explanation": {
            "base_value": 0.15,
            "shap_values": [...],
            ...
        },
        "recommendations": {
            "current_risk": 0.42,
            "actions": [...]
        }
    }
    """
    try:
        model_name = request.args.get('model_name', 'xgboost')
        date_index = int(request.args.get('date_index', -1))

        result = explain_athlete_risk(
            dataset_id=dataset_id,
            athlete_id=athlete_id,
            model_name=model_name,
            date_index=date_index
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in get_athlete_explanation: {str(e)}")
        return jsonify({"error": str(e)}), 500


def register_explainability_routes(app):
    """Register explainability blueprint with Flask app."""
    app.register_blueprint(explainability_bp)
    logger.info("Explainability routes registered")
