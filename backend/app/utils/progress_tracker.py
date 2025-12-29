import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import redis
import numpy as np


def numpy_to_python(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization.

    Handles: numpy.bool_, numpy.integer, numpy.floating, numpy.ndarray, and nested structures.
    """
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [numpy_to_python(item) for item in obj]
    return obj


class ProgressTracker:
    """Redis-backed job progress tracking."""

    _redis_client = None

    @classmethod
    def _get_client(cls):
        if cls._redis_client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            cls._redis_client = redis.from_url(redis_url, decode_responses=True)
        return cls._redis_client

    @classmethod
    def create_job(cls, job_type: str) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())[:8]
        job_data = {
            'id': job_id,
            'type': job_type,
            'status': 'pending',
            'progress': 0,
            'current_step': '',
            'total_steps': 0,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'data': {}
        }
        cls._get_client().set(f"job:{job_id}", json.dumps(job_data), ex=86400) # Expire in 24h
        return job_id

    @classmethod
    def start_job(cls, job_id: str, total_steps: int = 100):
        """Mark a job as started."""
        client = cls._get_client()
        data = client.get(f"job:{job_id}")
        if data:
            job_data = json.loads(data)
            job_data['status'] = 'running'
            job_data['started_at'] = datetime.utcnow().isoformat()
            job_data['total_steps'] = total_steps
            client.set(f"job:{job_id}", json.dumps(job_data), ex=86400)

    @classmethod
    def update_progress(cls, job_id: str, progress: int, current_step: str = '', **kwargs):
        """Update job progress."""
        client = cls._get_client()
        data = client.get(f"job:{job_id}")
        if data:
            job_data = json.loads(data)
            job_data['progress'] = min(progress, 100)
            job_data['current_step'] = current_step
            # Convert NumPy types to native Python types for JSON serialization
            job_data['data'].update(numpy_to_python(kwargs))
            client.set(f"job:{job_id}", json.dumps(job_data), ex=86400)

    @classmethod
    def complete_job(cls, job_id: str, result: Any = None):
        """Mark a job as completed."""
        client = cls._get_client()
        data = client.get(f"job:{job_id}")
        if data:
            job_data = json.loads(data)
            job_data['status'] = 'completed'
            job_data['progress'] = 100
            job_data['completed_at'] = datetime.utcnow().isoformat()
            # Convert NumPy types to native Python types for JSON serialization
            job_data['result'] = numpy_to_python(result)
            client.set(f"job:{job_id}", json.dumps(job_data), ex=86400)

    @classmethod
    def fail_job(cls, job_id: str, error: str):
        """Mark a job as failed."""
        client = cls._get_client()
        data = client.get(f"job:{job_id}")
        if data:
            job_data = json.loads(data)
            job_data['status'] = 'failed'
            job_data['completed_at'] = datetime.utcnow().isoformat()
            job_data['error'] = error
            client.set(f"job:{job_id}", json.dumps(job_data), ex=86400)

    @classmethod
    def cancel_job(cls, job_id: str):
        """Mark a job as cancelled."""
        client = cls._get_client()
        data = client.get(f"job:{job_id}")
        if data:
            job_data = json.loads(data)
            job_data['status'] = 'cancelled'
            job_data['completed_at'] = datetime.utcnow().isoformat()
            client.set(f"job:{job_id}", json.dumps(job_data), ex=86400)

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details."""
        data = cls._get_client().get(f"job:{job_id}")
        return json.loads(data) if data else None

    @classmethod
    def get_all_jobs(cls, job_type: Optional[str] = None) -> list:
        """Get all jobs, optionally filtered by type."""
        client = cls._get_client()
        keys = client.keys("job:*")
        jobs = []
        for key in keys:
            data = client.get(key)
            if data:
                job = json.loads(data)
                if job_type is None or job['type'] == job_type:
                    jobs.append(job)
        return sorted(jobs, key=lambda x: x['created_at'], reverse=True)

    @classmethod
    def is_running(cls, job_id: str) -> bool:
        """Check if a job is still running."""
        job = cls.get_job(job_id)
        return job is not None and job['status'] == 'running'

    @classmethod
    def cleanup_old_jobs(cls, max_age_hours: int = 24):
        """Redis handles expiration with TTL, but manual cleanup is possible."""
        pass
