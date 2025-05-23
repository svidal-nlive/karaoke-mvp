import os
import sys
import stat
import shutil
import tempfile
import argparse

EXCLUDED_DIRS = {'.git', 'node_modules', '.venv', '__pycache__'}
TARGET = 'chown -R ${APP_UID:-1000}:${APP_GID:-1000}'
REPLACEMENT = 'chown -R ${APP_UID:-1000}:${APP_GID:-1000}'

def is_regular_file(path):
    """Return True if path is a regular file (not dir, not link, not device, etc)."""
    try:
        mode = os.stat(path).st_mode
        return stat.S_ISREG(mode)
    except Exception:
        return False

def is_binary_file(filepath):
    """Guess if a file is binary by checking for null bytes in first 1024 bytes."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
    except Exception:
        return True
    return False

def safe_write(path, content):
    """Write content to path atomically."""
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp_file:
            tmp_file.write(content)
        shutil.move(tmp_path, path)
    except Exception as e:
        print(f"[ERROR] Could not write to {path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def patch_file(path, dry_run=False, backup=False):
    try:
        if not is_regular_file(path):
            return
        if is_binary_file(path):
            return
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if TARGET in content:
            print(f"[Would patch] {path}" if dry_run else f"[Patched] {path}")
            if not dry_run:
                if backup:
                    try:
                        shutil.copy2(path, path + '.bak')
                    except Exception as e:
                        print(f"[WARNING] Could not create backup for {path}: {e}")
                new_content = content.replace(TARGET, REPLACEMENT)
                safe_write(path, new_content)
    except PermissionError:
        print(f"[Skipped: PermissionError] {path}")
    except Exception as e:
        print(f"[Skipped: {type(e).__name__}] {path} ({e})")

def main(target_dir='.', dry_run=False, backup=True):
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            path = os.path.join(root, file)
            patch_file(path, dry_run=dry_run, backup=backup)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively replace 'chown -R ${APP_UID:-1000}:${APP_GID:-1000}' in files.")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be patched without writing changes.')
    parser.add_argument('--no-backup', action='store_true', help='Do not backup files before modifying.')
    parser.add_argument('dir', nargs='?', default='.', help='Directory to search (default: current)')
    args = parser.parse_args()
    # Flags below are always set by CLI args:
    DRY_RUN = args.dry_run
    BACKUP = not args.no_backup
    main(args.dir, dry_run=DRY_RUN, backup=BACKUP)
