import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import zipfile

import csv
import io
import json

TOKEN_PATTERN = re.compile(r'<Tkn\d{3}[A-Z]{5}Tkn>')
ALLOWED_EXTENSIONS = {'zip'}
MAX_DEPTH = 10

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def collect_files(zip_path, extract_dir, root_path="", depth=0):
    """Extracts zip file and collects all file paths up to MAX_DEPTH."""
    if depth > MAX_DEPTH:
        return []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:
        return []

    collected_files = []

    for dirpath, dirnames, filenames in os.walk(extract_dir):

        # print(f"Scanning {dirpath}, dirnames: {dirnames}, filenames: {filenames}")
        # print()

        for filename in filenames:

            absolute_file_path = os.path.join(dirpath, filename)
            internal_relative_path = os.path.relpath(absolute_file_path, extract_dir)
            relative_path = os.path.join(
                root_path, 
                internal_relative_path
            ) if root_path else internal_relative_path

            # print(f"File Name: {filename}")
            # print(f"Found file: (relative: {internal_relative_path}) root_path: {root_path})")
            # print()

            if allowed_file(filename):
                nested_extract_dir = os.path.join(
                    dirpath, 
                    filename + "_extracted"
                )
                os.makedirs(nested_extract_dir, exist_ok=True)
                # print(f"Created nested extract directory: {nested_extract_dir}")

                nested_files = collect_files(
                    absolute_file_path, 
                    nested_extract_dir, 
                    relative_path, 
                    depth + 1
                )

                collected_files.extend(nested_files)
            else:                
                collected_files.append({
                    "absolute_path": absolute_file_path, 
                    "relative_path": relative_path
                })

    return collected_files


def generate_csv(processed_results):
    if not processed_results:
        return None

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Path", "Token", "Occurrences"])

    writer.writerows(processed_results)

    output.seek(0)
    return output


def scan_file(file_path, relative_path):
    """Scans a single file for Tokens."""

    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
    except (IOError, OSError):
        return 0
    tokens = TOKEN_PATTERN.findall(content)

    if not tokens:
        return 0

    #  Counter gives: {"<Tkn435JFIRKTkn>": 5, "<Tkn111ABCDETkn>": 2}
    token_counts = Counter(tokens)

    results = []
    for token, count in token_counts.items():
        results.append((relative_path, token, count))
    
    return results

def process_files(collected_files):
    """Processes multiple files in parallel."""
    all_results = []
    with ProcessPoolExecutor() as executor:
        future_to_file = {
            executor.submit(scan_file, file["absolute_path"], file["relative_path"]): file
            for file in collected_files
        }
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                all_results.extend(result)

    all_results.sort(key=lambda x: (x[0], x[2], x[1]))

    global_counts = Counter()
    for rel_path, token, count in all_results:
        global_counts[token] += count
    

    print(json.dumps(dict(global_counts)))
    
    return dict(global_counts), all_results

