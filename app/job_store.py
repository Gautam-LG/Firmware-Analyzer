import uuid
import threading

_store = {} # { job_id: { 'status': 'pending' | 'completed', 'result': ... } }
_lock  = threading.Lock()

def create_job():
    """Create a new pending job. Return the job_id (string UUID)."""
    job_id = str(uuid.uuid4())
    with _lock:
        _store[job_id] = {"status": "pending", "result":None}
    return job_id;

def complete_job(job_id, result):
    """Mark job as completed with give result."""
    with _lock:
        _store[job_id]["status"] = "completed"
        _store[job_id]["result"] = result

def fail_job(job_id, error_message):
    """Mark job as failed."""
    with _lock:
        _store[job_id]["status"] = "failed"
        _store[job_id]["result"] = {"error": error_message}

def get_job(job_id):
    """Get job status and result. Returns None if job_id not found."""
    with _lock:
        return _store.get(job_id)
