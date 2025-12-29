import uuid
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import redis
import numpy as np

logger = logging.getLogger(__name__)


def numpy_to_python(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization.

    Handles: numpy.bool_, numpy.integer, numpy.floating, numpy.ndarray,
    numpy.str_, and nested structures (dicts, lists, tuples).
    """
    # Handle numpy scalar types first (check generic before specific)
    if isinstance(obj, (np.bool_, np.generic)):
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.str_):
            return str(obj)
        elif isinstance(obj, np.complexfloating):
            return complex(obj)
        else:
            # Fallback for any other numpy scalar
            return obj.item()
    elif isinstance(obj, np.ndarray):
        return [numpy_to_python(item) for item in obj.tolist()]
    elif isinstance(obj, dict):
        return {str(key): numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [numpy_to_python(item) for item in obj]
    elif hasattr(obj, 'tolist'):
        # Fallback for any object with tolist method (pandas Series, etc.)
        return numpy_to_python(obj.tolist())
    elif hasattr(obj, 'item'):
        # Fallback for any numpy-like scalar
        return obj.item()
    return obj


class ProgressTracker:
    """Redis-backed job progress tracking with atomic operations."""

    _redis_client = None
    _scripts = {}

    # Lua scripts for atomic operations
    _LUA_UPDATE_PROGRESS = """
    local key = KEYS[1]
    local data = redis.call('GET', key)
    if not data then
        return nil
    end
    local job = cjson.decode(data)
    job.progress = math.min(tonumber(ARGV[1]), 100)
    job.current_step = ARGV[2]
    if ARGV[3] and ARGV[3] ~= '{}' then
        local extra = cjson.decode(ARGV[3])
        for k, v in pairs(extra) do
            job.data[k] = v
        end
    end
    redis.call('SETEX', key, 86400, cjson.encode(job))
    return 1
    """

    _LUA_UPDATE_STATUS = """
    local key = KEYS[1]
    local data = redis.call('GET', key)
    if not data then
        return nil
    end
    local job = cjson.decode(data)
    job.status = ARGV[1]
    if ARGV[2] and ARGV[2] ~= '' then
        job.started_at = ARGV[2]
    end
    if ARGV[3] and ARGV[3] ~= '' then
        job.completed_at = ARGV[3]
    end
    if ARGV[4] and ARGV[4] ~= '' then
        job.total_steps = tonumber(ARGV[4])
    end
    if ARGV[5] and ARGV[5] ~= '' then
        job.progress = tonumber(ARGV[5])
    end
    if ARGV[6] and ARGV[6] ~= '' then
        job.error = ARGV[6]
    end
    if ARGV[7] and ARGV[7] ~= 'null' then
        job.result = cjson.decode(ARGV[7])
    end
    redis.call('SETEX', key, 86400, cjson.encode(job))
    return 1
    """

    @classmethod
    def _get_client(cls):
        if cls._redis_client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            cls._redis_client = redis.from_url(redis_url, decode_responses=True)
            # Register Lua scripts
            cls._scripts['update_progress'] = cls._redis_client.register_script(cls._LUA_UPDATE_PROGRESS)
            cls._scripts['update_status'] = cls._redis_client.register_script(cls._LUA_UPDATE_STATUS)
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
    def start_job(cls, job_id: str, total_steps: int = 100) -> bool:
        """Mark a job as started. Returns True if successful, False if job not found."""
        cls._get_client()  # Ensure scripts are registered
        result = cls._scripts['update_status'](
            keys=[f"job:{job_id}"],
            args=[
                'running',                          # status
                datetime.utcnow().isoformat(),      # started_at
                '',                                 # completed_at
                str(total_steps),                   # total_steps
                '',                                 # progress
                '',                                 # error
                'null'                              # result
            ]
        )
        if result is None:
            logger.warning(f"Attempted to start non-existent job: {job_id}")
            return False
        return True

    @classmethod
    def update_progress(cls, job_id: str, progress: int, current_step: str = '', **kwargs) -> bool:
        """Update job progress atomically. Returns True if successful, False if job not found."""
        cls._get_client()  # Ensure scripts are registered
        # Convert NumPy types to native Python types for JSON serialization
        extra_data = json.dumps(numpy_to_python(kwargs)) if kwargs else '{}'
        result = cls._scripts['update_progress'](
            keys=[f"job:{job_id}"],
            args=[str(progress), current_step, extra_data]
        )
        if result is None:
            logger.warning(f"Attempted to update progress for non-existent job: {job_id}")
            return False
        return True

    @classmethod
    def complete_job(cls, job_id: str, result: Any = None) -> bool:
        """Mark a job as completed atomically. Returns True if successful, False if job not found."""
        cls._get_client()  # Ensure scripts are registered
        # Convert NumPy types to native Python types for JSON serialization
        result_json = json.dumps(numpy_to_python(result)) if result is not None else 'null'
        script_result = cls._scripts['update_status'](
            keys=[f"job:{job_id}"],
            args=[
                'completed',                        # status
                '',                                 # started_at
                datetime.utcnow().isoformat(),      # completed_at
                '',                                 # total_steps
                '100',                              # progress
                '',                                 # error
                result_json                         # result
            ]
        )
        if script_result is None:
            logger.warning(f"Attempted to complete non-existent job: {job_id}")
            return False
        return True

    @classmethod
    def fail_job(cls, job_id: str, error: str) -> bool:
        """Mark a job as failed atomically. Returns True if successful, False if job not found."""
        cls._get_client()  # Ensure scripts are registered
        result = cls._scripts['update_status'](
            keys=[f"job:{job_id}"],
            args=[
                'failed',                           # status
                '',                                 # started_at
                datetime.utcnow().isoformat(),      # completed_at
                '',                                 # total_steps
                '',                                 # progress
                error,                              # error
                'null'                              # result
            ]
        )
        if result is None:
            logger.warning(f"Attempted to fail non-existent job: {job_id}")
            return False
        return True

    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        """Mark a job as cancelled atomically. Returns True if successful, False if job not found."""
        cls._get_client()  # Ensure scripts are registered
        result = cls._scripts['update_status'](
            keys=[f"job:{job_id}"],
            args=[
                'cancelled',                        # status
                '',                                 # started_at
                datetime.utcnow().isoformat(),      # completed_at
                '',                                 # total_steps
                '',                                 # progress
                '',                                 # error
                'null'                              # result
            ]
        )
        if result is None:
            logger.warning(f"Attempted to cancel non-existent job: {job_id}")
            return False
        return True

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
