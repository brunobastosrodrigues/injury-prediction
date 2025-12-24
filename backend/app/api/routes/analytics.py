from flask import Blueprint, request, jsonify
from ...services.analytics_service import AnalyticsService

bp = Blueprint('analytics', __name__)


@bp.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@bp.route('/distributions', methods=['GET'])
def get_distribution():
    """Get distribution data for a feature."""
    dataset_id = request.args.get('dataset_id')
    feature = request.args.get('feature')
    bins = request.args.get('bins', 50, type=int)

    if not dataset_id or not feature:
        return jsonify({'error': 'dataset_id and feature are required'}), 400

    data = AnalyticsService.get_distribution(dataset_id, feature, bins)

    if not data:
        return jsonify({'error': 'Dataset or feature not found'}), 404

    return jsonify(data)


@bp.route('/correlations', methods=['GET'])
def get_correlations():
    """Get correlation matrix."""
    dataset_id = request.args.get('dataset_id')
    features = request.args.getlist('features')

    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    data = AnalyticsService.get_correlations(dataset_id, features if features else None)

    if not data:
        return jsonify({'error': 'Dataset not found or insufficient features'}), 404

    return jsonify(data)


@bp.route('/pre-injury-window', methods=['GET'])
def get_pre_injury_window():
    """Get pre-injury window analysis."""
    dataset_id = request.args.get('dataset_id')
    lookback_days = request.args.get('lookback_days', 14, type=int)

    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    data = AnalyticsService.get_pre_injury_window(dataset_id, lookback_days)

    if not data:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify(data)


@bp.route('/athlete-timeline', methods=['GET'])
def get_athlete_timeline():
    """Get athlete time series data."""
    dataset_id = request.args.get('dataset_id')
    athlete_id = request.args.get('athlete_id')

    if not dataset_id or not athlete_id:
        return jsonify({'error': 'dataset_id and athlete_id are required'}), 400

    data = AnalyticsService.get_athlete_timeline(dataset_id, athlete_id)

    if not data:
        return jsonify({'error': 'Dataset or athlete not found'}), 404

    return jsonify(data)


@bp.route('/acwr-zones', methods=['GET'])
def get_acwr_zones():
    """Get ACWR zone analysis."""
    dataset_id = request.args.get('dataset_id')

    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    data = AnalyticsService.get_acwr_zones(dataset_id)

    if not data:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify(data)


@bp.route('/feature-importance', methods=['GET'])
def get_feature_importance():
    """Get feature importance from a model."""
    model_id = request.args.get('model_id')

    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400

    data = AnalyticsService.get_feature_importance(model_id)

    if not data:
        return jsonify({'error': 'Model not found'}), 404

    return jsonify(data)


@bp.route('/athletes', methods=['GET'])
def list_athletes():
    """List all athletes in a dataset."""
    dataset_id = request.args.get('dataset_id')

    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    athletes = AnalyticsService.list_athletes(dataset_id)

    if athletes is None:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify({'athletes': athletes})


@bp.route('/stats', methods=['GET'])
def get_dataset_stats():
    """Get overall dataset statistics."""
    dataset_id = request.args.get('dataset_id')

    if not dataset_id:
        return jsonify({'error': 'dataset_id is required'}), 400

    stats = AnalyticsService.get_dataset_stats(dataset_id)

    if not stats:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify(stats)


@bp.route('/simulate', methods=['POST'])
def simulate_intervention():
    """Simulate what-if intervention."""
    data = request.get_json() or {}
    model_id = data.get('model_id')
    athlete_id = data.get('athlete_id')
    date = data.get('date')
    overrides = data.get('overrides', {})

    if not all([model_id, athlete_id, date]):
        return jsonify({'error': 'model_id, athlete_id, and date are required'}), 400

    result = AnalyticsService.simulate_intervention(
        model_id=model_id,
        athlete_id=athlete_id,
        date=date,
        overrides=overrides
    )

    if not result:
        return jsonify({'error': 'Simulation failed. Check if model, athlete, and date exist.'}), 404

    return jsonify(result)
