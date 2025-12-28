from flask import Blueprint, request, jsonify
from ...services.preprocessing_service import PreprocessingService
from ..schemas import PreprocessingSchema
from pydantic import ValidationError

bp = Blueprint('preprocessing', __name__)


@bp.route('/run', methods=['POST'])
def run_preprocessing():
    """Start preprocessing pipeline."""
    try:
        data = request.get_json() or {}
        schema = PreprocessingSchema(**data)
    except ValidationError as e:
        return jsonify({'error': 'Validation Error', 'details': e.errors()}), 400

    job_id = PreprocessingService.preprocess_async(
        dataset_id=schema.dataset_id,
        split_strategy=schema.split_strategy,
        split_ratio=schema.split_ratio,
        prediction_window=schema.prediction_window,
        random_seed=schema.random_seed
    )

    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Started preprocessing dataset {schema.dataset_id}'
    }), 202


@bp.route('/<job_id>/status', methods=['GET'])
def get_preprocessing_status(job_id):
    """Get preprocessing job status."""
    status = PreprocessingService.get_preprocessing_status(job_id)

    if not status:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(status), 200


@bp.route('/splits', methods=['GET'])
def list_splits():
    """List all available preprocessed splits."""
    splits = PreprocessingService.list_splits()
    return jsonify({'splits': splits}), 200


@bp.route('/splits/<split_id>', methods=['GET'])
def get_split(split_id):
    """Get split details."""
    split = PreprocessingService.get_split(split_id)

    if not split:
        return jsonify({'error': 'Split not found'}), 404

    return jsonify(split), 200


@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all preprocessing jobs."""
    from ...utils.progress_tracker import ProgressTracker
    jobs = ProgressTracker.get_all_jobs('preprocessing')
    return jsonify({'jobs': jobs}), 200
