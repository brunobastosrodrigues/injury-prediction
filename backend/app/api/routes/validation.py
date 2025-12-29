"""
Validation API routes for Sim2Real experiments.

Provides endpoints to compare synthetic data against real PMData,
view distribution alignment, and run transfer learning experiments.
"""

from flask import Blueprint, jsonify, request

from ...services.validation_service import ValidationService
from ...utils.progress_tracker import ProgressTracker, numpy_to_python
from ...tasks import run_validation_task

validation_bp = Blueprint('validation', __name__)


# =========================================================================
# ASYNC VALIDATION ENDPOINTS (New)
# =========================================================================

@validation_bp.route('/run', methods=['POST'])
def start_validation():
    """
    Start an async validation job for a specific dataset.

    Request Body:
        dataset_id: str - The synthetic dataset to validate against PMData

    Returns:
        JSON with job_id and status.
    """
    try:
        data = request.get_json() or {}
        dataset_id = data.get('dataset_id')

        if not dataset_id:
            return jsonify({'error': 'dataset_id is required'}), 400

        # Check if dataset exists
        from ...services.validation_service import ValidationService
        df = ValidationService.load_synthetic_by_id(dataset_id)
        if df is None:
            return jsonify({'error': f'Dataset {dataset_id} not found'}), 404

        # Create job and start async task
        job_id = ProgressTracker.create_job('validation')
        run_validation_task.delay(job_id, dataset_id)

        return jsonify({
            'job_id': job_id,
            'dataset_id': dataset_id,
            'status': 'pending'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/jobs/<job_id>/status', methods=['GET'])
def get_validation_job_status(job_id):
    """
    Get status of a validation job.

    Returns:
        JSON with job status, progress, and result if completed.
    """
    try:
        job = ProgressTracker.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify(job), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/results', methods=['GET'])
def list_cached_validations():
    """
    List all datasets with cached validation results.

    Returns:
        JSON with list of validation summaries.
    """
    try:
        validations = ValidationService.list_cached_validations()
        return jsonify({'validations': validations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/results/<dataset_id>', methods=['GET'])
def get_cached_results(dataset_id):
    """
    Get cached validation results for a specific dataset.

    Returns:
        JSON with full validation results or 404 if not cached.
    """
    try:
        results = ValidationService.get_cached_results(dataset_id)
        if not results:
            return jsonify({
                'error': 'No cached results found',
                'dataset_id': dataset_id,
                'cached': False
            }), 404

        results['cached'] = True
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/results/<dataset_id>', methods=['DELETE'])
def delete_cached_results(dataset_id):
    """
    Delete cached validation results for a dataset (for recompute).

    Returns:
        JSON with success status.
    """
    try:
        deleted = ValidationService.delete_cached_results(dataset_id)
        return jsonify({
            'deleted': deleted,
            'dataset_id': dataset_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/jobs', methods=['GET'])
def list_validation_jobs():
    """
    List all validation jobs.

    Returns:
        JSON with list of jobs.
    """
    try:
        jobs = ProgressTracker.get_all_jobs('validation')
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =========================================================================
# METHODOLOGY VALIDATION ENDPOINTS (Publication-Quality)
# =========================================================================

@validation_bp.route('/methodology/run', methods=['POST'])
def run_methodology_validation():
    """
    Start methodology validation suite for a dataset.

    Request Body:
        dataset_id: str - The synthetic dataset to validate
        validation_types: list - Types to run: ['loso', 'sensitivity', 'equivalence']

    Returns:
        JSON with job_id and status.
    """
    try:
        from ...tasks import run_methodology_validation_task

        data = request.get_json() or {}
        dataset_id = data.get('dataset_id')
        validation_types = data.get('validation_types', ['loso', 'sensitivity', 'equivalence'])

        if not dataset_id:
            return jsonify({'error': 'dataset_id is required'}), 400

        # Validate types
        valid_types = {'loso', 'sensitivity', 'equivalence'}
        invalid = set(validation_types) - valid_types
        if invalid:
            return jsonify({'error': f'Invalid validation types: {invalid}'}), 400

        # Create job and start async task
        job_id = ProgressTracker.create_job('methodology_validation')
        run_methodology_validation_task.delay(job_id, dataset_id, validation_types)

        return jsonify({
            'job_id': job_id,
            'dataset_id': dataset_id,
            'validation_types': validation_types,
            'status': 'pending'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/methodology/summary/<dataset_id>', methods=['GET'])
def get_methodology_summary(dataset_id):
    """
    Get methodology validation summary for a dataset.

    Returns cached results for LOSO, Sensitivity Analysis, and Equivalence Check.
    """
    try:
        from ...services.methodology_validation import MethodologyValidationService
        summary = MethodologyValidationService.get_methodology_summary(dataset_id)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/methodology/loso/<dataset_id>', methods=['GET'])
def get_loso_results(dataset_id):
    """Get LOSO Cross-Validation results for a dataset."""
    try:
        from ...services.methodology_validation import MethodologyValidationService
        summary = MethodologyValidationService.get_methodology_summary(dataset_id)
        if summary['loso']['status'] == 'not_run':
            return jsonify({'error': 'LOSO validation not yet run', 'status': 'not_run'}), 404
        return jsonify(summary['loso']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/methodology/sensitivity/<dataset_id>', methods=['GET'])
def get_sensitivity_results(dataset_id):
    """Get Sensitivity Analysis results for a dataset."""
    try:
        from ...services.methodology_validation import MethodologyValidationService
        summary = MethodologyValidationService.get_methodology_summary(dataset_id)
        if summary['sensitivity']['status'] == 'not_run':
            return jsonify({'error': 'Sensitivity analysis not yet run', 'status': 'not_run'}), 404
        return jsonify(summary['sensitivity']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/methodology/equivalence', methods=['GET'])
def get_equivalence_results():
    """Get Rust-Python Equivalence Check results."""
    try:
        from ...services.methodology_validation import MethodologyValidationService
        # Equivalence is not dataset-specific, check any dataset
        import os
        cache_base = '/home/rodrigues/injury-prediction/data/validation'
        if os.path.exists(cache_base):
            for ds in os.listdir(cache_base):
                summary = MethodologyValidationService.get_methodology_summary(ds)
                if summary['equivalence']['status'] == 'complete':
                    return jsonify(summary['equivalence']), 200

        return jsonify({'error': 'Equivalence check not yet run', 'status': 'not_run'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =========================================================================
# LEGACY ENDPOINTS (Keep for backward compatibility)
# =========================================================================


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
            return jsonify(numpy_to_python(result)), 404
        return jsonify(numpy_to_python(result)), 200
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
            return jsonify(numpy_to_python(result)), 400
        return jsonify(numpy_to_python(result)), 200
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
            return jsonify(numpy_to_python(result)), 404
        return jsonify(numpy_to_python(result)), 200
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
            return jsonify(numpy_to_python(result)), 400
        return jsonify(numpy_to_python(result)), 200
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
            return jsonify(numpy_to_python(result)), 404
        return jsonify(numpy_to_python(result)), 200
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
        return jsonify(numpy_to_python(result)), 200
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
            return jsonify(numpy_to_python(result)), 404
        return jsonify(numpy_to_python(result)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =========================================================================
# SCIENTIFIC VALIDATION ENDPOINTS (Publication-Quality Rigor)
# =========================================================================

@validation_bp.route('/scientific/run', methods=['POST'])
def run_scientific_validation():
    """
    Start the scientific validation suite for a dataset.

    This runs hypothesis validation tests required for Nature Digital Medicine:
    - reproducibility: Multi-seed reproducibility audit (5 seeds)
    - permutation: Placebo control permutation test
    - sensitivity: Enhanced sensitivity analysis
    - adversarial: Adversarial fidelity check (Turing test)
    - null_models: Null model baseline comparison
    - subgroups: Subgroup generalization analysis

    Request Body:
        dataset_id: str - The synthetic dataset to validate
        tasks: list - Which tasks to run (optional, defaults to all)

    Returns:
        JSON with job_id and status.
    """
    try:
        from ...tasks import run_scientific_validation_task

        data = request.get_json() or {}
        dataset_id = data.get('dataset_id')
        tasks = data.get('tasks', [
            'reproducibility', 'permutation', 'sensitivity',
            'adversarial', 'null_models', 'subgroups'
        ])

        if not dataset_id:
            return jsonify({'error': 'dataset_id is required'}), 400

        # Validate task names
        valid_tasks = {
            'reproducibility', 'permutation', 'sensitivity',
            'adversarial', 'null_models', 'subgroups'
        }
        invalid = set(tasks) - valid_tasks
        if invalid:
            return jsonify({'error': f'Invalid tasks: {invalid}'}), 400

        # Create job and start async task
        job_id = ProgressTracker.create_job('scientific_validation')
        run_scientific_validation_task.delay(job_id, dataset_id, tasks)

        return jsonify({
            'job_id': job_id,
            'dataset_id': dataset_id,
            'tasks': tasks,
            'status': 'pending',
            'estimated_runtime': '15-30 minutes for full suite'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/scientific/jobs/<job_id>/status', methods=['GET'])
def get_scientific_job_status(job_id):
    """
    Get status of a scientific validation job.

    Returns:
        JSON with job status, progress, current task, and results if completed.
    """
    try:
        job = ProgressTracker.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify(job), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/scientific/results/<dataset_id>', methods=['GET'])
def get_scientific_results(dataset_id):
    """
    Get cached scientific validation results for a dataset.

    Returns:
        JSON with full scientific validation results or 404 if not cached.
    """
    try:
        from ...services.scientific_validation import ScientificValidationService

        results = ScientificValidationService.get_cached_results(dataset_id)
        if not results:
            return jsonify({
                'error': 'No cached results found',
                'dataset_id': dataset_id,
                'cached': False
            }), 404

        results['cached'] = True
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/scientific/results', methods=['GET'])
def list_scientific_validations():
    """
    List all datasets with cached scientific validation results.

    Returns:
        JSON with list of validation summaries.
    """
    try:
        import os
        from ...services.scientific_validation import ScientificValidationService

        cache_base = ScientificValidationService.CACHE_BASE
        validations = []

        if os.path.exists(cache_base):
            for dataset_id in os.listdir(cache_base):
                dataset_dir = os.path.join(cache_base, dataset_id)
                summary_path = os.path.join(dataset_dir, 'summary.json')

                if os.path.isdir(dataset_dir) and os.path.exists(summary_path):
                    try:
                        import json
                        with open(summary_path, 'r') as f:
                            summary = json.load(f)
                        validations.append({
                            'dataset_id': dataset_id,
                            'computed_at': summary.get('computed_at'),
                            'pass_rate': summary.get('pass_rate', 0),
                            'publication_ready': summary.get('publication_ready', False)
                        })
                    except Exception:
                        pass

        return jsonify({'validations': validations}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/scientific/results/<dataset_id>', methods=['DELETE'])
def delete_scientific_results(dataset_id):
    """
    Delete cached scientific validation results (for recompute).

    Returns:
        JSON with success status.
    """
    try:
        import os
        import shutil
        from ...services.scientific_validation import ScientificValidationService

        cache_dir = ScientificValidationService.get_cache_dir(dataset_id)

        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            return jsonify({
                'deleted': True,
                'dataset_id': dataset_id
            }), 200
        else:
            return jsonify({
                'deleted': False,
                'dataset_id': dataset_id,
                'message': 'No cached results found'
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/scientific/jobs', methods=['GET'])
def list_scientific_jobs():
    """
    List all scientific validation jobs.

    Returns:
        JSON with list of jobs.
    """
    try:
        jobs = ProgressTracker.get_all_jobs('scientific_validation')
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =========================================================================
# LANDING PAGE STATS ENDPOINT
# =========================================================================

@validation_bp.route('/landing-stats', methods=['GET'])
def get_landing_stats():
    """
    Get aggregated stats for the landing page from pre-seeded validation data.
    Uses dataset_pmdata_calibrated as the reference dataset.

    Returns:
        JSON with cohort info, ACWR zones, model performance, and three pillars.
    """
    import os
    import json
    from flask import current_app

    try:
        data_dir = current_app.config.get('DATA_DIR', 'data')
        validation_dir = os.path.join(data_dir, 'validation', 'dataset_pmdata_calibrated')
        models_dir = os.path.join(data_dir, 'models')

        stats = {
            'cohort': {
                'athletes': 1000,
                'samples': 366000,
                'year': 1
            },
            'acwr_zones': [],
            'model_performance': [],
            'three_pillars': {
                'statistical_fidelity': {'score': 0, 'status': 'pending'},
                'causal_fidelity': {'score': 0, 'status': 'pending'},
                'transferability': {'score': 0, 'status': 'pending'},
                'overall_score': 0,
                'pillars_passing': '0/3'
            }
        }

        # Load three pillars data
        three_pillars_path = os.path.join(validation_dir, 'three_pillars.json')
        if os.path.exists(three_pillars_path):
            with open(three_pillars_path, 'r') as f:
                tp_data = json.load(f)
                stats['three_pillars'] = {
                    'statistical_fidelity': tp_data.get('pillars', {}).get('statistical_fidelity', {}),
                    'causal_fidelity': tp_data.get('pillars', {}).get('causal_fidelity', {}),
                    'transferability': tp_data.get('pillars', {}).get('transferability', {}),
                    'overall_score': tp_data.get('overall_score', 0),
                    'pillars_passing': tp_data.get('pillars_passing', '0/3')
                }

        # Load causal mechanism data for ACWR zones
        causal_path = os.path.join(validation_dir, 'causal_mechanism.json')
        if os.path.exists(causal_path):
            with open(causal_path, 'r') as f:
                causal_data = json.load(f)
                stats['acwr_zones'] = causal_data.get('causal_asymmetry', {}).get('zones', [])
                stats['cohort']['athletes'] = causal_data.get('total_athletes', 1000)
                stats['cohort']['samples'] = causal_data.get('total_samples', 366000)

        # Load model performance from latest models
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith('.json')]
            model_results = {}

            for mf in model_files:
                with open(os.path.join(models_dir, mf), 'r') as f:
                    model_data = json.load(f)
                    model_type = model_data.get('model_type', '')
                    # Keep the latest model for each type
                    if model_type not in model_results or model_data.get('created_at', '') > model_results[model_type].get('created_at', ''):
                        model_results[model_type] = model_data

            # Format for landing page
            model_order = ['xgboost', 'random_forest', 'lasso']
            model_names = {'xgboost': 'XGBoost', 'random_forest': 'Random Forest', 'lasso': 'Lasso (L1)'}
            model_colors = {'xgboost': 'blue', 'random_forest': 'emerald', 'lasso': 'purple'}

            for mt in model_order:
                if mt in model_results:
                    metrics = model_results[mt].get('metrics', {})
                    stats['model_performance'].append({
                        'name': model_names.get(mt, mt),
                        'type': mt,
                        'auc': metrics.get('roc_auc', 0),
                        'color': model_colors.get(mt, 'gray')
                    })

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
