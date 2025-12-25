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
import json
import joblib

from app.utils.logger import get_logger

logger = get_logger(__name__)

explainability_bp = Blueprint('explainability', __name__, url_prefix='/api/explainability')


def load_model_info(model_id: str):
    """Load model metadata and paths."""
    models_dir = Path("/data/models")
    metadata_path = models_dir / f"{model_id}.json"
    model_path = models_dir / f"{model_id}.joblib"

    if not metadata_path.exists():
        return None, None, None

    with open(metadata_path) as f:
        metadata = json.load(f)

    split_id = metadata.get('split_id')
    processed_dir = Path("/data/processed") / split_id if split_id else None

    return metadata, model_path, processed_dir


def load_test_data(processed_dir: Path):
    """Load test data from processed directory."""
    X_test_path = processed_dir / "X_test.parquet"
    y_test_path = processed_dir / "y_test.parquet"

    if X_test_path.exists():
        X_test = pd.read_parquet(X_test_path)
    else:
        # Try CSV fallback
        X_test_csv = processed_dir / "X_test.csv"
        if X_test_csv.exists():
            X_test = pd.read_csv(X_test_csv)
        else:
            return None, None

    if y_test_path.exists():
        y_test = pd.read_parquet(y_test_path)
    else:
        y_test_csv = processed_dir / "y_test.csv"
        y_test = pd.read_csv(y_test_csv) if y_test_csv.exists() else None

    return X_test, y_test


@explainability_bp.route('/sample/<model_id>', methods=['GET'])
def get_sample_data(model_id: str):
    """
    Get a sample athlete data point from the model's test set.

    Returns a random high-risk sample for demonstration.
    """
    try:
        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        if not processed_dir or not processed_dir.exists():
            return jsonify({"error": "Processed data not found for this model"}), 404

        X_test, y_test = load_test_data(processed_dir)

        if X_test is None:
            return jsonify({"error": "Test data not found"}), 404

        # Try to get a high-risk sample for more interesting explanations
        if y_test is not None and len(y_test) > 0:
            # Get column name
            target_col = y_test.columns[0] if hasattr(y_test, 'columns') else 0
            high_risk_indices = y_test[y_test[target_col] == 1].index.tolist()

            if high_risk_indices:
                # Get a high-risk sample
                idx = high_risk_indices[len(high_risk_indices) // 2]  # Middle sample
                sample = X_test.loc[idx].to_dict()
            else:
                # Just get the last sample
                sample = X_test.iloc[-1].to_dict()
        else:
            sample = X_test.iloc[-1].to_dict()

        # Convert numpy types to Python types for JSON serialization
        sample = {k: float(v) if hasattr(v, 'item') else v for k, v in sample.items()}

        return jsonify({
            "sample": sample,
            "feature_names": list(X_test.columns),
            "model_id": model_id
        }), 200

    except Exception as e:
        logger.error(f"Error getting sample data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/explain/prediction', methods=['POST'])
def explain_prediction():
    """
    Generate SHAP explanation for a single prediction (Waterfall plot).
    """
    try:
        import shap

        data = request.json
        model_id = data.get('model_id')
        athlete_data = data.get('athlete_data')
        max_display = data.get('max_display', 10)

        if not model_id:
            return jsonify({"error": "model_id is required"}), 400

        if not athlete_data:
            return jsonify({"error": "athlete_data is required"}), 400

        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        # Load model
        model = joblib.load(model_path)

        # Prepare data
        X = pd.DataFrame([athlete_data])

        # Ensure columns match model's expected features
        feature_names = metadata.get('feature_names', list(X.columns))
        X = X.reindex(columns=feature_names, fill_value=0)

        # Create SHAP explainer
        model_type = metadata.get('model_type', 'xgboost')

        if model_type in ['xgboost', 'random_forest']:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            base_value = explainer.expected_value

            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # For binary classification, get positive class
            if isinstance(base_value, list):
                base_value = base_value[1]
        else:
            # Linear model
            explainer = shap.LinearExplainer(model, X)
            shap_values = explainer.shap_values(X)
            base_value = explainer.expected_value

        # Get prediction
        if hasattr(model, 'predict_proba'):
            prediction = float(model.predict_proba(X)[0, 1])
        else:
            prediction = float(model.predict(X)[0])

        # Sort by absolute SHAP value
        shap_vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
        feature_vals = X.values[0]

        sorted_indices = sorted(range(len(shap_vals)),
                               key=lambda i: abs(shap_vals[i]),
                               reverse=True)[:max_display]

        response = {
            "base_value": float(base_value) if hasattr(base_value, 'item') else base_value,
            "shap_values": [float(shap_vals[i]) for i in sorted_indices],
            "feature_values": [float(feature_vals[i]) for i in sorted_indices],
            "feature_names": [feature_names[i] for i in sorted_indices],
            "prediction": prediction,
            "explanation_type": "waterfall"
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in explain_prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/explain/global', methods=['POST'])
def explain_global():
    """
    Generate global SHAP explanation (feature importance).
    """
    try:
        import shap
        import numpy as np

        data = request.json
        model_id = data.get('model_id')
        sample_size = data.get('sample_size', 500)

        if not model_id:
            return jsonify({"error": "model_id is required"}), 400

        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        if not processed_dir or not processed_dir.exists():
            return jsonify({"error": "Processed data not found"}), 404

        # Load model and data
        model = joblib.load(model_path)
        X_test, _ = load_test_data(processed_dir)

        if X_test is None:
            return jsonify({"error": "Test data not found"}), 404

        # Sample data if too large
        if len(X_test) > sample_size:
            X_sample = X_test.sample(n=sample_size, random_state=42)
        else:
            X_sample = X_test

        # Create SHAP explainer
        model_type = metadata.get('model_type', 'xgboost')

        if model_type in ['xgboost', 'random_forest']:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.LinearExplainer(model, X_sample)
            shap_values = explainer.shap_values(X_sample)

        # Calculate mean absolute SHAP values
        mean_shap = np.abs(shap_values).mean(axis=0)
        feature_names = list(X_sample.columns)

        # Sort by importance
        sorted_indices = np.argsort(mean_shap)[::-1]

        response = {
            "mean_shap_values": [float(mean_shap[i]) for i in sorted_indices],
            "feature_names": [feature_names[i] for i in sorted_indices],
            "explanation_type": "global"
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in explain_global: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/explain/interactions', methods=['POST'])
def explain_interactions():
    """
    Generate SHAP dependence plot for interaction analysis.
    """
    try:
        import shap
        import numpy as np

        data = request.json
        model_id = data.get('model_id')
        feature1 = data.get('feature1')
        feature2 = data.get('feature2')
        sample_size = data.get('sample_size', 500)

        if not model_id or not feature1:
            return jsonify({"error": "model_id and feature1 are required"}), 400

        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        if not processed_dir or not processed_dir.exists():
            return jsonify({"error": "Processed data not found"}), 404

        # Load model and data
        model = joblib.load(model_path)
        X_test, _ = load_test_data(processed_dir)

        if X_test is None:
            return jsonify({"error": "Test data not found"}), 404

        # Check if feature exists
        if feature1 not in X_test.columns:
            return jsonify({"error": f"Feature '{feature1}' not found in data"}), 400

        # Sample data if too large
        if len(X_test) > sample_size:
            X_sample = X_test.sample(n=sample_size, random_state=42)
        else:
            X_sample = X_test

        # Create SHAP explainer
        model_type = metadata.get('model_type', 'xgboost')

        if model_type in ['xgboost', 'random_forest']:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.LinearExplainer(model, X_sample)
            shap_values = explainer.shap_values(X_sample)

        # Get feature index
        feature1_idx = list(X_sample.columns).index(feature1)
        feature1_values = X_sample[feature1].values
        feature1_shap = shap_values[:, feature1_idx]

        # Get interaction feature
        if feature2 and feature2 in X_sample.columns:
            feature2_values = X_sample[feature2].values
        else:
            # Auto-detect most interacting feature
            correlations = []
            for col in X_sample.columns:
                if col != feature1:
                    corr = np.corrcoef(feature1_shap, X_sample[col].values)[0, 1]
                    correlations.append((col, abs(corr) if not np.isnan(corr) else 0))
            correlations.sort(key=lambda x: x[1], reverse=True)
            feature2 = correlations[0][0] if correlations else feature1
            feature2_values = X_sample[feature2].values

        response = {
            "feature1_values": [float(v) for v in feature1_values],
            "shap_values": [float(v) for v in feature1_shap],
            "interaction_values": [float(v) for v in feature2_values],
            "feature1_name": feature1,
            "feature2_name": feature2,
            "explanation_type": "dependence"
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in explain_interactions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/counterfactuals', methods=['POST'])
def generate_counterfactuals():
    """
    Generate counterfactual explanations (What-If scenarios).
    """
    try:
        import numpy as np

        data = request.json
        model_id = data.get('model_id')
        athlete_data = data.get('athlete_data')
        desired_class = data.get('desired_class', 0)
        total_cfs = data.get('total_cfs', 3)

        if not model_id or not athlete_data:
            return jsonify({"error": "model_id and athlete_data are required"}), 400

        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        # Load model
        model = joblib.load(model_path)

        # Prepare data
        feature_names = metadata.get('feature_names', list(athlete_data.keys()))
        X = pd.DataFrame([athlete_data]).reindex(columns=feature_names, fill_value=0)

        # Get original prediction
        if hasattr(model, 'predict_proba'):
            original_pred = float(model.predict_proba(X)[0, 1])
        else:
            original_pred = float(model.predict(X)[0])

        # Generate simple counterfactuals by modifying important features
        # This is a simplified approach - for production, use dice-ml
        counterfactuals = []

        # Get feature importance from model or SHAP
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        else:
            importances = np.ones(len(feature_names)) / len(feature_names)

        # Sort features by importance
        sorted_features = sorted(zip(feature_names, importances),
                                key=lambda x: x[1], reverse=True)

        # Try modifying top features
        for i in range(min(total_cfs, len(sorted_features))):
            feature_name = sorted_features[i][0]
            original_value = X[feature_name].values[0]

            # Try different modifications
            for direction in [-1, 1]:
                X_cf = X.copy()

                # Modify the feature
                if original_value > 0:
                    new_value = original_value * (1 + direction * 0.2)
                else:
                    new_value = original_value + direction * 10

                X_cf[feature_name] = new_value

                # Check if prediction changes
                if hasattr(model, 'predict_proba'):
                    new_pred = float(model.predict_proba(X_cf)[0, 1])
                else:
                    new_pred = float(model.predict(X_cf)[0])

                # If this moves toward desired class, add it
                if (desired_class == 0 and new_pred < original_pred) or \
                   (desired_class == 1 and new_pred > original_pred):
                    counterfactuals.append({
                        "changes": {
                            feature_name: {
                                "from": float(original_value),
                                "to": float(new_value),
                                "change": float(new_value - original_value)
                            }
                        },
                        "predicted_risk": new_pred,
                        "risk_reduction": original_pred - new_pred
                    })
                    break

            if len(counterfactuals) >= total_cfs:
                break

        response = {
            "counterfactuals": counterfactuals,
            "original_prediction": original_pred,
            "total_scenarios": len(counterfactuals)
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in generate_counterfactuals: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@explainability_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """
    Generate actionable recommendations based on SHAP analysis.
    """
    try:
        import shap
        import numpy as np

        data = request.json
        model_id = data.get('model_id')
        athlete_data = data.get('athlete_data')
        risk_threshold = data.get('risk_threshold', 0.3)

        if not model_id or not athlete_data:
            return jsonify({"error": "model_id and athlete_data are required"}), 400

        metadata, model_path, processed_dir = load_model_info(model_id)

        if not metadata:
            return jsonify({"error": f"Model not found: {model_id}"}), 404

        # Load model
        model = joblib.load(model_path)

        # Prepare data
        feature_names = metadata.get('feature_names', list(athlete_data.keys()))
        X = pd.DataFrame([athlete_data]).reindex(columns=feature_names, fill_value=0)

        # Get prediction
        if hasattr(model, 'predict_proba'):
            current_risk = float(model.predict_proba(X)[0, 1])
        else:
            current_risk = float(model.predict(X)[0])

        # Get SHAP values
        model_type = metadata.get('model_type', 'xgboost')

        if model_type in ['xgboost', 'random_forest']:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.LinearExplainer(model, X)
            shap_values = explainer.shap_values(X)

        shap_vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values

        # Determine risk level
        if current_risk >= 0.5:
            risk_level = "high"
        elif current_risk >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Generate recommendations based on positive SHAP values (increasing risk)
        actions = []
        for i, (feature, shap_val) in enumerate(zip(feature_names, shap_vals)):
            if shap_val > 0.01:  # Feature increases risk
                current_value = float(X[feature].values[0])

                # Generate recommendation
                if 'stress' in feature.lower():
                    action = f"Reduce {feature.replace('_', ' ')}"
                    recommended_value = current_value * 0.8
                elif 'sleep' in feature.lower():
                    action = f"Increase {feature.replace('_', ' ')}"
                    recommended_value = current_value * 1.2
                elif 'load' in feature.lower() or 'tss' in feature.lower():
                    action = f"Reduce {feature.replace('_', ' ')}"
                    recommended_value = current_value * 0.85
                else:
                    action = f"Optimize {feature.replace('_', ' ')}"
                    recommended_value = current_value * 0.9

                actions.append({
                    "feature": feature,
                    "current_value": current_value,
                    "recommended_value": recommended_value,
                    "action": action,
                    "impact": float(shap_val),
                    "priority": "high" if shap_val > 0.05 else "medium"
                })

        # Sort by impact
        actions.sort(key=lambda x: x['impact'], reverse=True)
        actions = actions[:5]  # Top 5 recommendations

        response = {
            "current_risk": current_risk,
            "risk_level": risk_level,
            "message": f"Found {len(actions)} actionable recommendations to reduce injury risk.",
            "actions": actions
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def register_explainability_routes(app):
    """Register explainability blueprint with Flask app."""
    app.register_blueprint(explainability_bp)
    logger.info("Explainability routes registered")
