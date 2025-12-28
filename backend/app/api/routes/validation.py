"""
Validation API routes for Sim2Real experiments.

Provides endpoints to compare synthetic data against real PMData,
view distribution alignment, and run transfer learning experiments.
"""

from flask import Blueprint, jsonify

from ...services.validation_service import ValidationService

validation_bp = Blueprint('validation', __name__)


@validation_bp.route('/summary', methods=['GET'])
def get_validation_summary():
    """
    Get complete validation summary including distributions, Sim2Real, and PMData analysis.

    Returns:
        JSON with overall scores, distribution comparison, sim2real results, and PMData analysis.
    """
    try:
        summary = ValidationService.get_validation_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/distributions', methods=['GET'])
def get_distributions():
    """
    Compare distributions between synthetic and real PMData.

    Returns:
        JSON with JS divergence and histogram data for each feature.
    """
    try:
        result = ValidationService.get_distribution_comparison()
        if 'error' in result and not result.get('has_synthetic') or not result.get('has_pmdata'):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/sim2real', methods=['GET'])
def run_sim2real():
    """
    Run Sim2Real transfer learning experiment.

    Trains model on synthetic data, evaluates on real PMData.

    Returns:
        JSON with AUC, average precision, and interpretation.
    """
    try:
        result = ValidationService.run_sim2real_experiment()
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/pmdata-analysis', methods=['GET'])
def get_pmdata_analysis():
    """
    Analyze real PMData injury patterns.

    Returns:
        JSON with correlations, injury signature, and feature importance.
    """
    try:
        result = ValidationService.get_pmdata_analysis()
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/model-evaluation', methods=['GET'])
def get_model_evaluation():
    """
    Evaluate XGBoost models on PMData with different feature sets.

    Compares wellness-only, load-only, and combined models.

    Returns:
        JSON with AUC for each model and feature importance.
    """
    try:
        result = ValidationService.evaluate_pmdata_model()
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/status', methods=['GET'])
def get_validation_status():
    """
    Quick status check for validation data availability.

    Returns:
        JSON indicating if synthetic and PMData are available.
    """
    try:
        has_synthetic = ValidationService.load_synthetic() is not None
        has_pmdata = ValidationService.load_pmdata() is not None

        return jsonify({
            'has_synthetic': has_synthetic,
            'has_pmdata': has_pmdata,
            'ready': has_synthetic and has_pmdata
        })
    except Exception as e:
        return jsonify({'error': str(e), 'ready': False}), 500


# =========================================================================
# CAUSAL MECHANISM ANALYSIS ENDPOINTS (For Publication)
# =========================================================================

@validation_bp.route('/causal-mechanism', methods=['GET'])
def get_causal_mechanism():
    """
    Get comprehensive causal mechanism analysis for synthetic data.

    Validates the "Asymmetric ACWR" hypothesis and provides
    publication-quality metrics including:
    - Causal asymmetry by ACWR zone
    - Risk landscape data
    - Wellness vulnerability analysis
    - Load scenario analysis
    - Injury type breakdown

    Returns:
        JSON with complete causal mechanism analysis.
    """
    try:
        result = ValidationService.get_causal_mechanism_analysis()
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/three-pillars', methods=['GET'])
def get_three_pillars():
    """
    Get summary aligned with the Three Pillars of Validity framework.

    1. Statistical Fidelity: JS Divergence < 0.1 for wellness features
    2. Causal Fidelity: Undertrained zone shows 2-3x higher risk per load
    3. Transferability: Sim2Real AUC > 0.60

    Returns:
        JSON with pillar scores and overall publication readiness.
    """
    try:
        result = ValidationService.get_three_pillars_summary()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/raincloud/<feature>', methods=['GET'])
def get_raincloud_data(feature):
    """
    Get data for raincloud plot comparing synthetic vs real distributions.

    Args:
        feature: Feature name to compare (e.g., 'stress_score', 'sleep_quality_daily')

    Returns:
        JSON with density, box stats, and sample points for both datasets.
    """
    try:
        result = ValidationService.get_raincloud_data(feature)
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
