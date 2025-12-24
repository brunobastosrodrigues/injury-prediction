from flask import Blueprint, request, jsonify
from ...services.counterfactual_service import CounterfactualService

bp = Blueprint('counterfactuals', __name__)

@bp.route('/high-risk', methods=['GET'])
def get_high_risk_predictions():
    """Get high risk predictions for a model and split."""
    model_id = request.args.get('model_id')
    split_id = request.args.get('split_id')
    threshold = request.args.get('threshold', 0.5, type=float)

    if not model_id or not split_id:
        return jsonify({'error': 'model_id and split_id are required'}), 400

    try:
        results = CounterfactualService.get_high_risk_predictions(model_id, split_id, threshold)
        return jsonify(results)
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/generate', methods=['POST'])
def generate_counterfactuals():
    """Generate counterfactuals for a specific prediction."""
    data = request.get_json()
    model_id = data.get('model_id')
    split_id = data.get('split_id')
    instance_index = data.get('instance_index')

    if not model_id or not split_id or instance_index is None:
        return jsonify({'error': 'model_id, split_id, and instance_index are required'}), 400

    try:
        result = CounterfactualService.generate_counterfactuals(model_id, split_id, instance_index)
        if result is None:
            return jsonify({'error': 'Instance not found'}), 404
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
