# Firmware Analyzer

A Flask-based backend service for analyzing firmware files to detect tokens and generate analysis reports in CSV format. Supports both synchronous and asynchronous processing for flexibility in client implementations.

## Features

- **Synchronous Analysis**: Analyze firmware and retrieve results immediately
- **Asynchronous Analysis**: Submit long-running analysis jobs and poll for results
- **Recursive ZIP Extraction**: Support nested ZIP archives up to configurable depth
- **Token Detection**: Identify security tokens using regex patterns
- **Parallel Processing**: Multi-threaded file scanning for improved performance
- **CSV Export**: Generate detailed analysis reports in CSV format
- **Job Management**: Track asynchronous job status and results

## Prerequisites

- Python 3.7+
- Flask 2.0+
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Firmware-Analyzer"
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Update `run.py` to customize the service:

```python
app.run(host="0.0.0.0", port=5000, debug=True)
```

- `host`: Bind address (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)
- `port`: Service port (default: 5000)
- `debug`: Enable debug mode (set to False in production)

## Running the Service

```bash
python run.py
```

The service will start at `http://localhost:5000`

## API Documentation

### 1. Synchronous Analysis

**Endpoint:** `POST /analyze`

Analyze firmware file and return results immediately. Best for smaller files.

**Request:**
```bash
curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze
```

**Response (Success - 200):**
```json
{
  "collected_files": [
    {"absolute_path": "...", "relative_path": "..."},
    ...
  ],
  "processed_results": [
    ["path/to/file", "<Tkn123ABCDETkn>", 5],
    ...
  ]
}
```

**Response (CSV Download):**
```bash
curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze -OJ
```
Downloads `results.csv` with columns: Path, Token, Occurrences

### 2. Asynchronous Analysis (Submit Job)

**Endpoint:** `POST /analyze/async`

Submit a firmware file for background processing. Returns immediately with a job ID.

**Request:**
```bash
curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze/async
```

**Response (Accepted - 202):**
```json
{
  "JOB_ID": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. Check Job Status

**Endpoint:** `GET /results/<job_id>`

Poll for asynchronous job status and results.

**Request:**
```bash
curl -X GET http://localhost:5000/results/550e8400-e29b-41d4-a716-446655440000
```

**Response (Pending - 200):**
```json
{
  "Status": "Pending"
}
```

**Response (Completed - 200):**
```json
{
  "Status": "completed",
  "Results": {
    "tokens": {
      "<Tkn123ABCDETkn>": 5,
      "<Tkn456FGHIJTkn>": 3
    },
    "details": [
      {"path": "file.c", "token": "<Tkn123ABCDETkn>", "occurrences": 5},
      ...
    ]
  }
}
```

**Response (Failed - 200):**
```json
{
  "Status": "failed",
  "Results": {
    "error": "Error message describing the failure"
  }
}
```

### 4. Download Results

**Endpoint:** `GET /results/<job_id>/download`

Download analysis results as CSV file from a completed job.

**Request:**
```bash
curl -X GET http://localhost:5000/results/550e8400-e29b-41d4-a716-446655440000/download -OJ
```

**Response (Success - 200):**
Downloads `results.csv` file

**Response (Pending - 200):**
```json
{
  "Status": "Pending"
}
```

## Architecture

```
Firmware Analyzer Service
├── Routes (routes.py)
│   ├── POST /analyze (sync)
│   ├── POST /analyze/async (submit)
│   ├── GET /results/<job_id> (status)
│   └── GET /results/<job_id>/download (CSV export)
├── Analyzer (analyzer.py)
│   ├── Token pattern matching
│   ├── File collection (recursive ZIP extraction)
│   ├── Parallel file scanning
│   └── CSV generation
├── Job Store (job_store.py)
│   └── In-memory job status tracking
└── Thread Pool Executor
    └── Async job worker pool
```

## Quick CURL CMDs to test APIs:

```sh

curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze

curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze -OJ

curl -X POST -F "firmware=@firmware_analyzer_test.zip" http://localhost:5000/analyze/async

curl -X GET http://localhost:5000/reults/<job_id>

curl -X GET http://localhost:5000/reults/<job_id>/download -OJ

```
