import os
import argparse
import shutil
import logging
from shared.pipeline_utils import redis_client, notify_all

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

# --- Config (now supports ENV for all paths) ---
PIPELINE_CLEAN_TARGETS = {
    "metadata": os.environ.get("META_DIR", "/metadata/json"),
    "queue": os.environ.get("QUEUE_DIR", "/queue"),
    "stems": os.environ.get("STEMS_DIR", "/stems"),
    "output": os.environ.get("OUTPUT_DIR", "/output"),
}
SUFFIX_MAP = {
    "metadata": [".mp3.json", "_cover.jpg"],
    "queue": [".mp3"],
    "stems": [""],  # directories named after song
    "output": ["_karaoke.mp3"],
}


def list_cleanable_files():
    """
    Return a list of (stage, path_to_delete) for completed files no longer in active Redis states.
    """
    clean_targets = []
    organized_files = redis_client.keys("file:*")
    organized = set()
    for k in organized_files:
        data = redis_client.hgetall(k)
        if data.get("status") == "organized":
            base = k.replace("file:", "")
            namebase = os.path.splitext(base)[0]
            organized.add(namebase)
    for stage, dir_path in PIPELINE_CLEAN_TARGETS.items():
        abs_dir = dir_path
        if not os.path.exists(abs_dir):
            continue
        for item in os.listdir(abs_dir):
            item_path = os.path.join(abs_dir, item)
            if stage == "stems":
                namebase = item
            else:
                for suffix in SUFFIX_MAP[stage]:
                    if item.endswith(suffix):
                        namebase = item.replace(suffix, "")
                        break
                else:
                    continue
            if namebase in organized:
                clean_targets.append(item_path)
    return clean_targets


def main():
    parser = argparse.ArgumentParser(description="Cleanup residual pipeline files.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually delete files/dirs (otherwise dry run)",
    )
    args = parser.parse_args()

    files_to_delete = list_cleanable_files()
    if not files_to_delete:
        print("Nothing to clean.")
        return

    if args.live:
        print("=== LIVE CLEANUP: Deleting the following ===")
        for path in files_to_delete:
            try:
                if os.path.isfile(path):
                    print(f"Deleting file: {path}")
                    os.remove(path)
                elif os.path.isdir(path):
                    print(f"Deleting directory: {path}")
                    shutil.rmtree(path)
                notify_all("Maintenance Cleaned File", f"🧹 Deleted: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")
                notify_all("Maintenance Error", f"❌ Error deleting {path}: {e}")
        print("Cleanup complete.")
    else:
        print("=== DRY RUN: Files/directories that would be cleaned up ===")
        for path in files_to_delete:
            print(path)


if __name__ == "__main__":
    main()
