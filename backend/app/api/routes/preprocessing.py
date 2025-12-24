from flask import Blueprint, request, jsonify
from ...services.preprocessing_service import PreprocessingService

bp = Blueprint('preprocessing', __name__)


@bp.route('/run', methods=['POST'])
def run_preprocessing():
    """Start preprocessing pipeline."""
    data = request.get_json() or {}

    dataset_id = data.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    split_strategy = data.get('split_strategy', 'athlete_based')
    if split_strategy not in ['athlete_based', 'time_based']:
        return jsonify({'error': 'split_strategy must be athlete_based or time_based'}), 400

    split_ratio = data.get('split_ratio', 0.2)
    prediction_window = data.get('prediction_window', 7)
    random_seed = data.get('random_seed', 42)

    job_id = PreprocessingService.preprocess_async(
        dataset_id=dataset_id,
        split_strategy=split_strategy,
        split_ratio=split_ratio,
        prediction_window=prediction_window,
        random_seed=random_seed
    )

    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Started preprocessing dataset {dataset_id}'
    }), 202


@bp.route('/<job_id>/status', methods=['GET'])
def get_preprocessing_status(job_id):
    """Get preprocessing job status."""
    status = PreprocessingService.get_preprocessing_status(job_id)

    if not status:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(status)


@bp.route('/splits', methods=['GET'])
def list_splits():
    """List all available preprocessed splits."""
    splits = PreprocessingService.list_splits()
    return jsonify({'splits': splits})


@bp.route('/splits/<split_id>', methods=['GET'])
def get_split(split_id):
    """Get split details."""
    split = PreprocessingService.get_split(split_id)

    if not split:
        return jsonify({'error': 'Split not found'}), 404

    return jsonify(split)


@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all preprocessing jobs."""
    from ...utils.progress_tracker import ProgressTracker
    jobs = ProgressTracker.get_all_jobs('preprocessing')
    return jsonify({'jobs': jobs})
