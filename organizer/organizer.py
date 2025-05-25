import os
import shutil
import threading
import time
import json
import logging
from flask import Flask
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

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
ORG_DIR = os.environ.get("ORG_DIR", "/organized")
META_DIR = os.environ.get("META_DIR", "/metadata/json")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))


def get_metadata_from_json(file_path):
    """Reads artist/album/title metadata from JSON file, or uses defaults."""
    base = os.path.basename(file_path)
    json_file = os.path.join(META_DIR, base.replace("_karaoke.mp3", ".mp3.json"))
    if os.path.exists(json_file):
        try:
            with open(json_file, encoding="utf-8") as f:
                meta = json.load(f)
            artist = str(meta.get("TPE1", "") or "UnknownArtist")
            album = str(meta.get("TALB", "") or "UnknownAlbum")
            title = str(meta.get("TIT2", "") or os.path.splitext(base)[0])
            return artist, album, title
        except Exception:
            pass
    return "UnknownArtist", "UnknownAlbum", os.path.splitext(base)[0]


def is_valid_karaoke_mp3(filename):
    """Checks if a file is a karaoke mp3 by naming convention."""
    return filename.endswith("_karaoke.mp3")


def organize_file(file_path, file):
    try:
        artist, album, title = get_metadata_from_json(file_path)
        artist = clean_string(artist)
        album = clean_string(album)
        title = clean_string(title)
        out_dir = os.path.join(ORG_DIR, artist, album)
        os.makedirs(out_dir, exist_ok=True)
        dest_file = os.path.join(out_dir, os.path.basename(file_path))
        if not os.path.exists(dest_file):
            shutil.copy2(file_path, dest_file)
            notify_all(
                "Karaoke Pipeline Success",
                f"🎵 Karaoke organized: {os.path.basename(file_path)} → {artist}/{album}",
            )
    except Exception as e:
        tb = traceback.format_exc()
        timestamp = datetime.datetime.now().isoformat()
        error_details = f"{timestamp}\nException: {e}\n\nTraceback:\n{tb}"
        set_file_error(file, error_details)
        notify_all(
            "Karaoke Pipeline Error", f"Organizer error for {file} at {timestamp}:\n{e}"
        )
        redis_client.incr(f"organizer_retries:{file}")


def run_organizer():
    os.makedirs(ORG_DIR, exist_ok=True)
    while True:
        files = get_files_by_status("packaged")
        for file in files:
            file_path = os.path.join(OUTPUT_DIR, file.replace(".mp3", "_karaoke.mp3"))
            if not (
                is_valid_karaoke_mp3(os.path.basename(file_path))
                and os.path.exists(file_path)
            ):
                continue

            def org_func():
                organize_file(file_path, file)
                set_file_status(file, "organized")

            try:
                handle_auto_retry(
                    "organizer", file, func=org_func, max_retries=MAX_RETRIES
                )
            except Exception as e:
                tb = traceback.format_exc()
                timestamp = datetime.datetime.now().isoformat()
                error_details = f"{timestamp}\nException: {e}\n\nTraceback:\n{tb}"
                set_file_error(file, error_details)
                notify_all(
                    "Karaoke Pipeline Error",
                    f"Organizer error for {file} at {timestamp}:\n{e}",
                )
                redis_client.incr(f"organizer_retries:{file}")
        time.sleep(10)


app = Flask(__name__)


@app.route("/health")
def health():
    return "ok", 200


if __name__ == "__main__":
    t = threading.Thread(target=run_organizer, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
