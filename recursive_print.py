import os
import argparse

# --- Configuration ---
INCLUDE_TYPES = ['Dockerfile'] #, '.py', '.txt', '.log', '.yml', '.env', '.gitignore', '.dockerignore']
EXCLUDE_DIRS_CONTENT = ['node_modules', 'build', '.git', 'deemix_config', 'doublecommander_config', 'grafana_data', 'jellyfin']
EXCLUDE_DIRS_TREE = ['node_modules', 'build', '.git', 'deemix_config', 'doublecommander_config', 'grafana_data', 'jellyfin']
# ---------------------

def should_exclude(path_parts, exclude_list):
    return any(part in exclude_list for part in path_parts)

def print_tree(root, prefix=""):
    """Recursively print directory tree, respecting EXCLUDE_DIRS_TREE and PermissionError."""
    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        print(prefix + '[Permission Denied]: ' + os.path.basename(root))
        return
    entries = [e for e in entries if not e == os.path.basename(__file__)]
    for index, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = '└── ' if index == len(entries) - 1 else '├── '
        print(prefix + connector + name)
        if os.path.isdir(path):
            rel_parts = os.path.relpath(path, start=BASE_DIR).split(os.sep)
            if should_exclude(rel_parts, EXCLUDE_DIRS_TREE):
                continue
            extension = '    ' if index == len(entries) - 1 else '│   '
            print_tree(path, prefix + extension)

def print_contents(root):
    """Find and print contents of files matching INCLUDE_TYPES, skipping EXCLUDE_DIRS_CONTENT and handling PermissionError."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda e: print(f"[Permission Denied]: {e.filename}")):
        # Skip excluded directories
        rel_dir = os.path.relpath(dirpath, start=BASE_DIR)
        parts = rel_dir.split(os.sep) if rel_dir != '.' else []
        if should_exclude(parts, EXCLUDE_DIRS_CONTENT):
            dirnames[:] = []  # Don't descend into excluded dirs
            continue

        for filename in filenames:
            file_ext = os.path.splitext(filename)[1]
            if (file_ext in INCLUDE_TYPES) or (filename in INCLUDE_TYPES):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), start=BASE_DIR)
                print(f"\n=== {rel_path} ===")
                try:
                    with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as f:
                        print(f.read())
                except PermissionError:
                    print(f"[Permission Denied]: {rel_path}")
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Recursively print tree and contents of selected files."
    )
    parser.add_argument(
        'target', nargs='?', default='.',
        help='Target directory to scan (default: current directory)'
    )
    args = parser.parse_args()

    global BASE_DIR
    BASE_DIR = os.path.abspath(args.target)

    print(BASE_DIR)
    print_tree(BASE_DIR)
    print_contents(BASE_DIR)

if __name__ == '__main__':
    main()
