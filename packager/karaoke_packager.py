import os
import json
import logging
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from pydub import AudioSegment
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

# --- Config: override via ENV ---
STEMS_DIR = os.environ.get("STEMS_DIR", "/stems")
META_DIR = os.environ.get("META_DIR", "/metadata/json")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 5))


def robust_load_metadata(meta_path):
    """Load metadata JSON, falling back to defaults if not present."""
    fallback = {
        "TIT2": "Unknown Title",
        "TPE1": "Unknown Artist",
        "TALB": "Unknown Album",
    }
    if not os.path.exists(meta_path):
        logger.warning(f"Metadata file missing: {meta_path}")
        return fallback
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        for k in fallback:
            if k not in meta or not meta[k]:
                meta[k] = fallback[k]
        return meta
    except Exception as e:
        logger.error(f"Metadata JSON error in {meta_path}: {e}")
        return fallback


def clean_mp3_tags(mp3_path, meta):
    audio = MP3(mp3_path)
    audio.delete()
    audio.save()
    audio = MP3(mp3_path, ID3=ID3)
    try:
        audio.add_tags()
    except Exception:
        pass
    audio.tags.add(TIT2(encoding=3, text=meta.get("TIT2")))
    audio.tags.add(TPE1(encoding=3, text=meta.get("TPE1")))
    audio.tags.add(TALB(encoding=3, text=meta.get("TALB")))
    audio.save()


def apply_metadata(instrumental_path, meta_path, out_path):
    audio = AudioSegment.from_wav(instrumental_path)
    audio.export(out_path, format="mp3")
    meta = robust_load_metadata(meta_path)
    clean_mp3_tags(out_path, meta)
    cover_path = meta_path.replace(".json", "_cover.jpg")
    if os.path.exists(cover_path):
        audiofile = MP3(out_path, ID3=ID3)
        with open(cover_path, "rb") as albumart:
            audiofile.tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=albumart.read(),
                )
            )
        audiofile.save()


def run_packager():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    while True:
        files = get_files_by_status("split")
        for file in files:
            song_name = clean_string(os.path.splitext(file)[0])
            inst_path = os.path.join(STEMS_DIR, song_name, "accompaniment.wav")
            meta_path = os.path.join(META_DIR, f"{song_name}.mp3.json")
            out_path = os.path.join(OUTPUT_DIR, f"{song_name}_karaoke.mp3")

            if not os.path.exists(inst_path):
                set_file_error(file, f"Missing accompaniment.wav for {song_name}")
                continue
            if not os.path.exists(meta_path):
                set_file_error(file, f"Missing metadata JSON for {song_name}")
                continue
            if os.path.exists(out_path):
                set_file_status(file, "packaged")
                continue

            def package_func():
                apply_metadata(inst_path, meta_path, out_path)
                set_file_status(file, "packaged")
                redis_client.delete(f"packager_retries:{file}")
                notify_all(
                    "Karaoke Pipeline Success",
                    f"✅ Karaoke track produced: {os.path.basename(out_path)}",
                )

            try:
                handle_auto_retry(
                    "packager",
                    file,
                    func=package_func,
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
                    f"❌ Packaging failed for {song_name}: {e}",
                )
                redis_client.incr(f"packager_retries:{file}")
        time.sleep(2)


if __name__ == "__main__":
    run_packager()
