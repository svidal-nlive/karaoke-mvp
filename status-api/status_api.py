import os
import logging
import time
from flask import Flask, jsonify, request, Response
from shared.pipeline_utils import (
    redis_client,
    get_files_by_status,
    set_file_status,
    notify_all,
)

# Logging config
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "HEALTH": logging.INFO,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

# Pipeline directories: allow override from env
PIPELINE_STAGES = [
    ("input", "INPUT_DIR", ".mp3"),
    ("queued", "QUEUE_DIR", ".ready"),
    ("metadata_extracted", "META_DIR", ".json"),
    ("split", "STEMS_DIR", ""),
    ("packaged", "OUTPUT_DIR", ".mp3"),
    ("organized", "ORG_DIR", ".mp3"),
    ("error", "QUEUE_DIR", ".error"),
]
DIRS = {
    stage: os.environ.get(env_key, default_path)
    for (stage, env_key, default_path) in [
        ("input", "INPUT_DIR", "/input"),
        ("queued", "QUEUE_DIR", "/queue"),
        ("metadata_extracted", "META_DIR", "/metadata/json"),
        ("split", "STEMS_DIR", "/stems"),
        ("packaged", "OUTPUT_DIR", "/output"),
        ("organized", "ORG_DIR", "/organized"),
        ("error", "QUEUE_DIR", "/queue"),
    ]
}


def list_files(directory, suffix):
    """List files in directory with optional suffix filtering."""
    if not os.path.exists(directory):
        return []
    if suffix:
        return [f for f in os.listdir(directory) if f.endswith(suffix)]
    else:
        return os.listdir(directory)


def get_file_status(filename):
    """Return status and last error for the given file from Redis and file system."""
    stages = {}
    namebase = os.path.splitext(filename)[0]
    for stage, dirkey, suffix in PIPELINE_STAGES:
        dirpath = DIRS[stage]
        for f in list_files(dirpath, suffix):
            if namebase in f:
                stages[stage] = os.path.join(dirpath, f)
    redis_data = redis_client.hgetall(f"file:{filename}")
    status = redis_data.get("status", "unknown")
    last_error = redis_data.get("error", "")
    return {
        "filename": filename,
        "stages": stages,
        "status": status,
        "last_error": last_error,
    }


app = Flask(__name__)


@app.route("/health")
def health():
    """Healthcheck endpoint."""
    return "ok", 200


@app.route("/status")
def status():
    all_bases = set()
    for stage, dirkey, suf in PIPELINE_STAGES:
        for f in list_files(DIRS[stage], suf):
            all_bases.add(os.path.splitext(f)[0])
    file_statuses = [get_file_status(f"{b}.mp3") for b in all_bases]
    return jsonify({"files": file_statuses})


@app.route("/error-files")
def error_files():
    error_files = get_files_by_status("error")
    details = [get_file_status(f) for f in error_files]
    return jsonify({"error_files": details})


@app.route("/retry", methods=["POST"])
def retry_file():
    data = request.json
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    filekey = f"file:{filename}"
    if not redis_client.exists(filekey):
        return jsonify({"error": "File not found"}), 404
    set_file_status(filename, "queued")
    for stage in ["metadata", "splitter", "packager", "organizer"]:
        redis_client.delete(f"{stage}_retries:{filename}")
    redis_client.hdel(filekey, "error")
    notify_all("File Retry Triggered", f"🔄 File {filename} reset to queued and retries cleared.")
    return jsonify({"message": f"File {filename} reset to queued and retries cleared."})


@app.route("/pipeline-health")
def pipeline_health():
    stages = ["queued", "metadata_extracted", "split", "packaged", "organized", "error"]
    counts = {stage: len(get_files_by_status(stage)) for stage in stages}
    return jsonify(counts)


@app.route("/error-details/<filename>")
def error_details(filename):
    filekey = f"file:{filename}"
    error = redis_client.hget(filekey, "error")
    if not error:
        return jsonify({"filename": filename, "error": "No error found."}), 404
    return jsonify({"filename": filename, "error": error})


start_time = time.time()


@app.route("/metrics")
def metrics():
    stages = ["queued", "metadata_extracted", "split", "packaged", "organized", "error"]
    metrics_lines = []
    for stage in stages:
        count = len(get_files_by_status(stage))
        metrics_lines.append(f"karaoke_files_{stage} {count}")
    uptime = int(time.time() - start_time)
    metrics_lines.append(f"karaoke_statusapi_uptime_seconds {uptime}")
    return Response("\n".join(metrics_lines), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
