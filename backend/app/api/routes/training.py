from flask import Blueprint, request, jsonify
from ...services.training_service import TrainingService

bp = Blueprint('training', __name__)


@bp.route('/train', methods=['POST'])
def train_models():
    """Start model training."""
    data = request.get_json() or {}

    split_id = data.get('split_id')
    if not split_id:
        return jsonify({'error': 'split_id is required'}), 400

    model_types = data.get('models', ['random_forest'])
    valid_types = ['lasso', 'random_forest', 'xgboost']
    for mt in model_types:
        if mt not in valid_types:
            return jsonify({'error': f'Invalid model type: {mt}. Valid types: {valid_types}'}), 400

    hyperparameters = data.get('hyperparameters')

    job_id = TrainingService.train_async(
        split_id=split_id,
        model_types=model_types,
        hyperparameters=hyperparameters
    )

    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Started training {len(model_types)} model(s)'
    }), 202


@bp.route('/<job_id>/status', methods=['GET'])
def get_training_status(job_id):
    """Get training job status."""
    status = TrainingService.get_training_status(job_id)

    if not status:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(status)


@bp.route('/models', methods=['GET'])
def list_models():
    """List all trained models."""
    models = TrainingService.list_models()
    return jsonify({'models': models})


@bp.route('/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Get model details."""
    model = TrainingService.get_model(model_id)

    if not model:
        return jsonify({'error': 'Model not found'}), 404

    return jsonify(model)


@bp.route('/models/<model_id>/roc-curve', methods=['GET'])
def get_roc_curve(model_id):
    """Get ROC curve data."""
    split_id = request.args.get('split_id')
    if not split_id:
        # Try to get from model metadata
        model = TrainingService.get_model(model_id)
        if model:
            split_id = model.get('split_id')

    if not split_id:
        return jsonify({'error': 'split_id is required'}), 400

    curve_data = TrainingService.get_roc_curve(model_id, split_id)

    if not curve_data:
        return jsonify({'error': 'Could not generate ROC curve'}), 404

    return jsonify(curve_data)


@bp.route('/models/<model_id>/pr-curve', methods=['GET'])
def get_pr_curve(model_id):
    """Get Precision-Recall curve data."""
    split_id = request.args.get('split_id')
    if not split_id:
        model = TrainingService.get_model(model_id)
        if model:
            split_id = model.get('split_id')

    if not split_id:
        return jsonify({'error': 'split_id is required'}), 400

    curve_data = TrainingService.get_pr_curve(model_id, split_id)

    if not curve_data:
        return jsonify({'error': 'Could not generate PR curve'}), 404

    return jsonify(curve_data)


@bp.route('/compare', methods=['POST'])
def compare_models():
    """Compare multiple models."""
    data = request.get_json() or {}
    model_ids = data.get('model_ids', [])

    if len(model_ids) < 2:
        return jsonify({'error': 'At least 2 model_ids required for comparison'}), 400

    comparison = TrainingService.compare_models(model_ids)
    return jsonify(comparison)


@bp.route('/model-types', methods=['GET'])
def get_model_types():
    """Get available model types and their default parameters."""
    return jsonify({'model_types': TrainingService.MODEL_TYPES})


@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all training jobs."""
    from ...utils.progress_tracker import ProgressTracker
    jobs = ProgressTracker.get_all_jobs('training')
    return jsonify({'jobs': jobs})
