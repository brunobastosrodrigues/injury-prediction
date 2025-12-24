from flask import Blueprint, request, jsonify
from ...services.data_generation_service import DataGenerationService

bp = Blueprint('data_generation', __name__)


@bp.route('/generate', methods=['POST'])
def generate_dataset():
    """Start generating a new synthetic dataset."""
    data = request.get_json() or {}

    n_athletes = data.get('n_athletes', 100)
    simulation_year = data.get('simulation_year', 2024)
    random_seed = data.get('random_seed', 42)
    injury_config = data.get('injury_config')

    # Validate parameters
    if not isinstance(n_athletes, int) or n_athletes < 1 or n_athletes > 5000:
        return jsonify({'error': 'n_athletes must be between 1 and 5000'}), 400

    if not isinstance(simulation_year, int) or simulation_year < 2000 or simulation_year > 2030:
        return jsonify({'error': 'simulation_year must be between 2000 and 2030'}), 400

    # Start async generation
    job_id = DataGenerationService.generate_dataset_async(
        n_athletes=n_athletes,
        simulation_year=simulation_year,
        random_seed=random_seed,
        injury_config=injury_config
    )

    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Started generating dataset with {n_athletes} athletes'
    }), 202


@bp.route('/generate/<job_id>/status', methods=['GET'])
def get_generation_status(job_id):
    """Get the status of a data generation job."""
    status = DataGenerationService.get_generation_status(job_id)

    if not status:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(status)


@bp.route('/generate/<job_id>/cancel', methods=['POST'])
def cancel_generation(job_id):
    """Cancel a running data generation job."""
    success = DataGenerationService.cancel_generation(job_id)

    if success:
        return jsonify({'status': 'cancelled', 'message': 'Job cancelled successfully'})
    else:
        return jsonify({'error': 'Job not found or not running'}), 400


@bp.route('/datasets', methods=['GET'])
def list_datasets():
    """List all available datasets."""
    datasets = DataGenerationService.list_datasets()
    return jsonify({'datasets': datasets})


@bp.route('/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get dataset details and summary statistics."""
    dataset = DataGenerationService.get_dataset(dataset_id)

    if not dataset:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify(dataset)


@bp.route('/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """Delete a dataset."""
    success = DataGenerationService.delete_dataset(dataset_id)

    if success:
        return jsonify({'status': 'deleted', 'message': 'Dataset deleted successfully'})
    else:
        return jsonify({'error': 'Dataset not found'}), 404


@bp.route('/datasets/<dataset_id>/sample', methods=['GET'])
def get_dataset_sample(dataset_id):
    """Get a sample of data from a dataset."""
    table = request.args.get('table', 'daily_data')
    n_rows = request.args.get('n_rows', 100, type=int)

    if table not in ['athletes', 'daily_data', 'activity_data']:
        return jsonify({'error': 'Invalid table name'}), 400

    sample = DataGenerationService.get_dataset_sample(dataset_id, table, n_rows)

    if not sample:
        return jsonify({'error': 'Dataset or table not found'}), 404

    return jsonify(sample)


@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all data generation jobs."""
    from ...utils.progress_tracker import ProgressTracker
    jobs = ProgressTracker.get_all_jobs('data_generation')
    return jsonify({'jobs': jobs})
