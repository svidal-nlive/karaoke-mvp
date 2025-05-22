import os
import argparse

# --- Configuration ---
# File extensions or names to include in content printing
INCLUDE_TYPES = ['.py'] #, '.txt', '.log', '.yml', 'Dockerfile', '.env']
# Directories to exclude from content search (and their children)
EXCLUDE_DIRS_CONTENT = ['node_modules', 'build', '.git', 'deemix_config', 'doublecommander_config']
# Directories to exclude from tree printing (and their children)
EXCLUDE_DIRS_TREE = ['node_modules', 'build', '.git', 'deemix_config', 'doublecommander_config']
# ---------------------

def should_exclude(path_parts, exclude_list):
    """
    Return True if any element in path_parts matches an exclusion.
    """
    return any(part in exclude_list for part in path_parts)


def print_tree(root, prefix=""):
    """Recursively print directory tree, respecting EXCLUDE_DIRS_TREE."""
    entries = sorted(os.listdir(root))
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
    """Find and print contents of files matching INCLUDE_TYPES, skipping EXCLUDE_DIRS_CONTENT."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        rel_dir = os.path.relpath(dirpath, start=BASE_DIR)
        parts = rel_dir.split(os.sep) if rel_dir != '.' else []
        if should_exclude(parts, EXCLUDE_DIRS_CONTENT):
            dirnames[:] = []  # Don't descend into excluded dirs
            continue

        for filename in filenames:
            file_ext = os.path.splitext(filename)[1]
            # Match by extension or exact name (Dockerfile)
            if (file_ext in INCLUDE_TYPES) or (filename in INCLUDE_TYPES):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), start=BASE_DIR)
                print(f"\n=== {rel_path} ===")
                try:
                    with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as f:
                        print(f.read())
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

    # Print tree
    print(BASE_DIR)
    print_tree(BASE_DIR)

    # Print file contents
    print_contents(BASE_DIR)


if __name__ == '__main__':
    main()
