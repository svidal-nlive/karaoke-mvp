import os
import json
import logging
import threading
import time
from flask import Flask
from mutagen.mp3 import MP3
from shared.pipeline_utils import (
    set_file_status,
    get_files_by_status,
    set_file_error,
    notify_all,
    clean_string,
    redis_client,
    handle_auto_retry,
)
import traceback
import datetime

QUEUE_DIR = os.environ.get("QUEUE_DIR", "/queue")
META_DIR = os.environ.get("META_DIR", "/metadata/json")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 5))


def extract_metadata(mp3_path):
    """
    Extract MP3 metadata using mutagen.
    Returns a dictionary of tags or None on failure.
    """
    try:
        audio = MP3(mp3_path)
        tags = audio.tags
        meta = {}
        meta["TIT2"] = (
            clean_string(tags.get("TIT2", "Unknown Title")) if tags else "Unknown Title"
        )
        meta["TPE1"] = (
            clean_string(tags.get("TPE1", "Unknown Artist"))
            if tags
            else "Unknown Artist"
        )
        meta["TALB"] = (
            clean_string(tags.get("TALB", "Unknown Album")) if tags else "Unknown Album"
        )
        if tags:
            meta["TRCK"] = clean_string(tags.get("TRCK", ""))
        return meta
    except Exception as e:
        logging.error(f"Metadata extraction failed for {mp3_path}: {e}")
        return None


def run_extractor():
    """
    Main extractor loop. Processes files in 'queued' status,
    extracts metadata, and writes to META_DIR as JSON.
    """
    os.makedirs(META_DIR, exist_ok=True)
    while True:
        files = get_files_by_status("queued")
        for file in files:
            file_path = os.path.join(QUEUE_DIR, clean_string(file))
            if not os.path.exists(file_path):
                set_file_error(file, "File not found for metadata extraction")
                continue

            # Retry block now actually runs the metadata extraction
            def extract_and_store():
                meta = extract_metadata(file_path)
                if meta is not None:
                    meta_path = os.path.join(
                        META_DIR, os.path.splitext(file)[0] + ".mp3.json"
                    )
                    with open(meta_path, "w") as f:
                        json.dump(meta, f)
                    set_file_status(file, "metadata_extracted")
                    redis_client.delete(f"metadata_retries:{file}")
                    logging.info(f"Metadata extracted and status set for {file}")
                else:
                    raise Exception("Metadata extraction returned None")

            try:
                handle_auto_retry(
                    "metadata",
                    file,
                    func=extract_and_store,
                    max_retries=MAX_RETRIES,
                    retry_delay=RETRY_DELAY,
                )
            except Exception as e:
                tb = traceback.format_exc()
                timestamp = datetime.datetime.now().isoformat()
                error_details = f"{timestamp}\nException: {e}\n\nTraceback:\n{tb}"
                set_file_error(file, error_details)
                notify_all(
                    "Karaoke Pipeline Error",
                    f"❌ Metadata extraction failed for {file}: {e}",
                )
                redis_client.incr(f"metadata_retries:{file}")
        time.sleep(2)


app = Flask(__name__)


@app.route("/health")
def health():
    """Healthcheck endpoint for Docker health probe."""
    return "ok", 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    t = threading.Thread(target=run_extractor, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
