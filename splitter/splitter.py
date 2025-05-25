import os
import time
import logging
import tempfile
import subprocess
from pydub import AudioSegment
from pydub.utils import make_chunks
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

QUEUE_DIR = os.environ.get("QUEUE_DIR", "/queue")
STEMS_DIR = os.environ.get("STEMS_DIR", "/stems")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))
CHUNK_LENGTH_MS = int(os.environ.get("CHUNK_LENGTH_MS", 30000))


def process_file(file_path, song_name):
    """Split an MP3 into stems in chunks, merge results, write output."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            audio = AudioSegment.from_file(file_path)
            chunks = make_chunks(audio, CHUNK_LENGTH_MS)
            vocals = AudioSegment.empty()
            accompaniment = AudioSegment.empty()
            with tempfile.TemporaryDirectory() as temp_dir:
                for idx, chunk in enumerate(chunks):
                    chunk_path = os.path.join(temp_dir, f"chunk_{idx}.mp3")
                    chunk.export(chunk_path, format="mp3")
                    output_dir = os.path.join(temp_dir, f"output_{idx}")
                    os.makedirs(output_dir, exist_ok=True)
                    result = subprocess.run(
                        [
                            "spleeter",
                            "separate",
                            "-p",
                            "spleeter:2stems",
                            "-o",
                            output_dir,
                            chunk_path,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if result.returncode != 0:
                        raise RuntimeError(
                            f"Spleeter error (chunk {idx}): {result.stderr}"
                        )
                    stem_dir = os.path.join(output_dir, f"chunk_{idx}")
                    vocals_path = os.path.join(stem_dir, "vocals.wav")
                    acc_path = os.path.join(stem_dir, "accompaniment.wav")
                    if not (os.path.exists(vocals_path) and os.path.exists(acc_path)):
                        raise FileNotFoundError(
                            f"Missing stems for chunk {idx}: {vocals_path}, {acc_path}"
                        )
                    vocals_chunk = AudioSegment.from_wav(vocals_path)
                    accompaniment_chunk = AudioSegment.from_wav(acc_path)
                    vocals += vocals_chunk
                    accompaniment += accompaniment_chunk
                out_dir = os.path.join(STEMS_DIR, song_name)
                os.makedirs(out_dir, exist_ok=True)
                vocals.export(os.path.join(out_dir, "vocals.wav"), format="wav")
                accompaniment.export(
                    os.path.join(out_dir, "accompaniment.wav"), format="wav"
                )
            return True
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return str(e)


def main():
    while True:
        files = get_files_by_status("metadata_extracted")
        for file in files:
            file_path = os.path.join(QUEUE_DIR, clean_string(file))
            song_name = os.path.splitext(file)[0]
            if not os.path.exists(file_path):
                set_file_error(file, "File not found for splitting")
                continue

            def process_func():
                result = process_file(file_path, clean_string(song_name))
                if result is True:
                    set_file_status(file, "split")
                    redis_client.delete(f"splitter_retries:{file}")
                    notify_all(
                        "Karaoke Pipeline Success", f"✅ Split completed for {file}"
                    )
                else:
                    raise Exception(result)
                return True

            try:
                handle_auto_retry(
                    "splitter",
                    file,
                    func=process_func,
                    max_retries=MAX_RETRIES,
                    retry_delay=RETRY_DELAY,
                )
            except Exception as e:
                tb = traceback.format_exc()
                timestamp = datetime.datetime.now().isoformat()
                error_details = f"{timestamp}\nSplitter error: {e}\n\nTraceback:\n{tb}"
                set_file_error(file, error_details)
                notify_all(
                    "Karaoke Pipeline Error", f"❌ Splitter failed for {file}: {e}"
                )
                redis_client.incr(f"splitter_retries:{file}")
        time.sleep(5)


if __name__ == "__main__":
    main()
