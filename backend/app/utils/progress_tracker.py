import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional


class ProgressTracker:
    """Thread-safe in-memory job progress tracking."""

    _jobs: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def create_job(cls, job_type: str) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())[:8]
        with cls._lock:
            cls._jobs[job_id] = {
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
        return job_id

    @classmethod
    def start_job(cls, job_id: str, total_steps: int = 100):
        """Mark a job as started."""
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]['status'] = 'running'
                cls._jobs[job_id]['started_at'] = datetime.utcnow().isoformat()
                cls._jobs[job_id]['total_steps'] = total_steps

    @classmethod
    def update_progress(cls, job_id: str, progress: int, current_step: str = '', **kwargs):
        """Update job progress."""
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]['progress'] = min(progress, 100)
                cls._jobs[job_id]['current_step'] = current_step
                cls._jobs[job_id]['data'].update(kwargs)

    @classmethod
    def complete_job(cls, job_id: str, result: Any = None):
        """Mark a job as completed."""
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]['status'] = 'completed'
                cls._jobs[job_id]['progress'] = 100
                cls._jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
                cls._jobs[job_id]['result'] = result

    @classmethod
    def fail_job(cls, job_id: str, error: str):
        """Mark a job as failed."""
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]['status'] = 'failed'
                cls._jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
                cls._jobs[job_id]['error'] = error

    @classmethod
    def cancel_job(cls, job_id: str):
        """Mark a job as cancelled."""
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]['status'] = 'cancelled'
                cls._jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details."""
        with cls._lock:
            return cls._jobs.get(job_id, None)

    @classmethod
    def get_all_jobs(cls, job_type: Optional[str] = None) -> list:
        """Get all jobs, optionally filtered by type."""
        with cls._lock:
            jobs = list(cls._jobs.values())
            if job_type:
                jobs = [j for j in jobs if j['type'] == job_type]
            return sorted(jobs, key=lambda x: x['created_at'], reverse=True)

    @classmethod
    def is_running(cls, job_id: str) -> bool:
        """Check if a job is still running."""
        job = cls.get_job(job_id)
        return job is not None and job['status'] == 'running'

    @classmethod
    def cleanup_old_jobs(cls, max_age_hours: int = 24):
        """Remove jobs older than max_age_hours."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        with cls._lock:
            old_jobs = [
                job_id for job_id, job in cls._jobs.items()
                if datetime.fromisoformat(job['created_at']) < cutoff
            ]
            for job_id in old_jobs:
                del cls._jobs[job_id]
