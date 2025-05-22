import os
import argparse
import shutil
import logging
from shared.pipeline_utils import redis_client, clean_string

# Logging for troubleshooting
logging.basicConfig(level=logging.INFO)

# --- Config ---
PIPELINE_CLEAN_TARGETS = {
    "metadata": "/metadata/json",
    "queue": "/queue",
    "stems": "/stems",
    "output": "/output",
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
    # Get all organized files from redis (finished files)
    organized_files = redis_client.keys("file:*")
    organized = set()
    for k in organized_files:
        data = redis_client.hgetall(k)
        if data.get("status") == "organized":
            base = k.replace("file:", "")
            namebase = os.path.splitext(base)[0]
            organized.add(namebase)

    # Now scan all cleanup dirs for files/dirs that match these organized bases
    for stage, dir_path in PIPELINE_CLEAN_TARGETS.items():
        abs_dir = dir_path
        if not os.path.exists(abs_dir):
            continue
        # Handle both files and dirs depending on stage
        for item in os.listdir(abs_dir):
            item_path = os.path.join(abs_dir, item)
            # For stems (dirs), rest are files
            if stage == "stems":
                namebase = item
            else:
                # Try to match file base
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
            if os.path.isfile(path):
                print(f"Deleting file: {path}")
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting file {path}: {e}")
            elif os.path.isdir(path):
                print(f"Deleting directory: {path}")
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    print(f"Error deleting dir {path}: {e}")
        print("Cleanup complete.")
    else:
        print("=== DRY RUN: Files/directories that would be cleaned up ===")
        for path in files_to_delete:
            print(path)


if __name__ == "__main__":
    main()
