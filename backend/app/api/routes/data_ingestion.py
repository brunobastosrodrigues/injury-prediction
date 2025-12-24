from flask import Blueprint, request, jsonify, current_app
from ...services.ingestion_service import IngestionService
from ..schemas import IngestionSchema
from pydantic import ValidationError
import os
import uuid

bp = Blueprint('data_ingestion', __name__)

@bp.route('/ingest', methods=['POST'])
def ingest_real_data():
    """Endpoint to ingest real-world athlete data (FIT, CSV, etc)."""
    try:
        form_data = request.form.to_dict()
        schema = IngestionSchema(**form_data)
    except ValidationError as e:
        return jsonify({'error': 'Validation Error', 'details': e.errors()}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save file temporarily
    temp_dir = os.path.join(current_app.config['DATA_DIR'], 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(temp_dir, f"{file_id}{ext}")
    file.save(file_path)
    
    # Start async ingestion
    job_id = IngestionService.ingest_data_async(schema.dataset_id, file_path, schema.data_type)
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Started ingesting real data into dataset {schema.dataset_id}'
    }), 202
