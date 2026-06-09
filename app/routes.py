import io
import os
import tempfile
import shutil
from flask import Blueprint, request, jsonify, send_file

from app.analyzer import process_files, generate_csv, collect_files, allowed_file
from app.job_store import create_job, complete_job, fail_job, get_job
from app import executor
from functools import wraps

bp = Blueprint('api', __name__)

def _format_details(results):
    """Convert list of tuples to list of dicts for JSON response."""
    return [
        {"path": path, "token": token, "occurrences": count}
        for path, token, count in results
    ]

def _unformat_details(results):
    """Convert list of dicts to list of tuples."""
    return [
        (item["path"], item["token"], item["occurrences"])
        for item in results
    ]

def firmware_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'firmware' not in request.files:
            return jsonify({"error": "No firmware found in the request"}), 400

        file = request.files['firmware']
        
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type"}), 400
        
        return f(file, *args, **kwargs)
    return decorated_function


@bp.route('/analyze', methods=['POST'])
@firmware_required
def analyze_sync(file):
    """Accepts a firmware zip file path on clients disk, analyzes it, returns JSON results and a CSV file."""
    
    
    collected_files = []
    processed_results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, file.filename)
        file.save(zip_path)

        extracted_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extracted_dir, exist_ok=True)

        collected_files = collect_files(zip_path, extracted_dir)
        _, processed_results = process_files(collected_files)
        csv_output = generate_csv(processed_results)

        if csv_output:
            return send_file(
                io.BytesIO(csv_output.getvalue().encode("utf-8")),
                mimetype='text/csv',
                as_attachment=True,
                download_name='results.csv'
            )

    return jsonify({"collected_files": collected_files, "processed_results": processed_results}), 200

@bp.route('/analyze/async', methods=['POST'])
@firmware_required
def analyze_async(file):
    """Accepts a firmware zip file path on clients disk, analyzes it asynchronously, returns a Job ID."""
    
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, file.filename)
    file.save(zip_path)

    job_id = create_job()

    executor.submit(_run_analysis_job, job_id, temp_dir, zip_path)

    return jsonify({"JOB_ID":job_id}), 202

    
def _run_analysis_job(job_id, temp_dir, zip_path):
    """Background worker function for async analysis."""
    try:
        extracted_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extracted_dir, exist_ok=True)

        collected_files = collect_files(zip_path, extracted_dir)
        global_countes, processed_results = process_files(collected_files)

        complete_job(job_id,{
                     "tokens": global_countes,
                     "details": _format_details(processed_results)                    
                    })
    except Exception as e:
        fail_job(job_id, str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    

@bp.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """Poll for Job results."""
    job = get_job(job_id)

    if not job:
        return jsonify({"error": "Job Not Found"}), 404
    
    if job["status"] == "pending":
        return jsonify({"Status":"Pending"}), 200
    
    if job["status"] == "failed":
        return jsonify({"Status":"Failed"}), 200
    
    return jsonify({"Status":job["status"], "Results":job["result"]}), 200



@bp.route('/results/<job_id>/download', methods=['GET'])
def download_results(job_id):
    """Poll for Job results."""
    job = get_job(job_id)

    if not job:
        return jsonify({"error": "Job Not Found"}), 404
    
    if job["status"] == "pending":
        return jsonify({"Status":"Pending"}), 200
    
    if job["status"] == "failed":
        return jsonify({"Status":"Failed"}), 200

    data = _unformat_details(job["result"]["details"])
    csv_output = generate_csv(data)

    if csv_output:
        return send_file(
            io.BytesIO(csv_output.getvalue().encode("utf-8")),
            mimetype='text/csv',
            as_attachment=True,
            download_name='results.csv'
        )
    
    return jsonify({"Status":job["status"], "Results":job["result"]}), 200