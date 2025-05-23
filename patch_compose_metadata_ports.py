#!/usr/bin/env python3
import re
import sys
import argparse
from pathlib import Path

# Files to patch (all docker-compose YAMLs in current dir)
COMPOSE_SUFFIXES = [
    'docker-compose.yml',
    'docker-compose.override.yml',
    'docker-compose.prod.yml',
    'docker-compose.staging.yml',
    'docker-compose.staging.override.yml',
    'docker-compose.pull.yml',
    'docker-compose.ci.yml',
    'docker-compose.ci.override.yml',
    'docker-compose.build.yml',
    'docker-compose.support.yml',
    'docker-compose.dev.yml',
]

def find_compose_files():
    files = []
    for pat in COMPOSE_SUFFIXES:
        f = Path(pat)
        if f.exists():
            files.append(f)
    # Also catch docker-compose*.yml
    for f in Path('.').glob('docker-compose*.yml'):
        if f not in files:
            files.append(f)
    for f in Path('.').glob('docker-compose*.override.yml'):
        if f not in files:
            files.append(f)
    return files

def process_file(path, dry=False):
    original = Path(path).read_text()
    lines = original.splitlines()
    output = []
    in_volumes_block = False
    indent = ""
    global_volumes = []
    metadata_json_present = False
    metadata_present = False
    metadata_json_used = False
    metadata_used = False
    referenced_metadata_json = False

    # First pass: collect which volumes are present in the 'volumes:' block at root
    for i, line in enumerate(lines):
        if re.match(r"^volumes:\s*$", line):
            in_volumes_block = True
            indent = re.match(r"^(\s*)volumes:", line).group(1) + "  "
            continue
        if in_volumes_block:
            if re.match(r"^\S", line):  # Next root key
                in_volumes_block = False
                continue
            m = re.match(rf"^{indent}(\w+):", line)
            if m:
                v = m.group(1)
                if v == 'metadata_json':
                    metadata_json_present = True
                if v == 'metadata':
                    metadata_present = True
                global_volumes.append(v)
    # Second pass: do replacements and note usage
    for i, line in enumerate(lines):
        orig = line
        # Only replace '- metadata:/metadata' with '- metadata_json:/metadata/json' (with leading whitespace)
        pat = r"^(\s*)- metadata:/metadata\s*$"
        repl = r"\1- metadata_json:/metadata/json"
        if re.match(pat, line):
            line = re.sub(pat, repl, line)
            referenced_metadata_json = True
            metadata_used = True  # We're replacing a usage
        # Remove '- metadata:' (used as a volume, not a mount)
        pat2 = r"^(\s*)- metadata:\s*$"
        if re.match(pat2, line):
            metadata_used = True  # Track old usage for later cleanup
            # Remove line by not adding to output
            continue
        # Remove empty or commented metadata service stub
        pat3 = r"^\s*- metadata:\s*"
        if re.match(pat3, line):
            continue
        # Mark if metadata_json is used
        if re.match(r"^(\s*)- metadata_json:/metadata/json", line):
            referenced_metadata_json = True
        # Replace 'metadata:' key in root volumes block
        # (handled in cleanup later)
        output.append(line)

    # Third pass: clean up root 'volumes:' block and add metadata_json: if needed
    new_lines = []
    in_volumes_block = False
    skip_next = False
    for i, line in enumerate(output):
        if skip_next:
            skip_next = False
            continue
        if re.match(r"^volumes:\s*$", line):
            in_volumes_block = True
            new_lines.append(line)
            continue
        if in_volumes_block:
            # If we hit a non-indented line, we're done
            if re.match(r"^\S", line) and not re.match(r"^volumes:", line):
                in_volumes_block = False
                new_lines.append(line)
                continue
            # Remove 'metadata:' if unused
            if re.match(r"^\s*metadata:\s*$", line) and not metadata_used:
                continue
            # If only 'metadata:' remains and not used, skip
            if re.match(r"^\s*metadata:\s*$", line):
                continue
            # If block is now empty, remove volumes:
            # But wait for later...
            new_lines.append(line)
        else:
            new_lines.append(line)
    # Check if we need to add metadata_json: to volumes
    # Add at end of volumes block if referenced and not present
    if referenced_metadata_json and not metadata_json_present:
        # Find where 'volumes:' block ends
        for i, line in enumerate(new_lines):
            if re.match(r"^volumes:\s*$", line):
                # Find where block ends
                j = i+1
                while j < len(new_lines) and (re.match(r"^\s", new_lines[j]) or new_lines[j] == ""):
                    j += 1
                new_lines.insert(j, "  metadata_json:")
                break

    # Final pass: clean up empty volumes block (just 'volumes:' and no children)
    cleaned_lines = []
    skip = False
    for i, line in enumerate(new_lines):
        if skip:
            skip = False
            continue
        if re.match(r"^volumes:\s*$", line):
            # Check next lines for indentation
            if i+1 >= len(new_lines) or not re.match(r"^\s", new_lines[i+1]):
                # next is not indented, remove
                skip = False
                continue
            # Or if next is empty
            if i+1 < len(new_lines) and new_lines[i+1].strip() == "":
                skip = True
                continue
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines) + "\n"
    # Print diff if dry
    if dry and original != result:
        print(f"[Would patch] {path}")
        from difflib import unified_diff
        diff = list(unified_diff(
            original.splitlines(keepends=True),
            result.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"{path} (patched)",
        ))
        print(''.join(diff))
    # Actually write if not dry
    if not dry and original != result:
        Path(path).write_text(result)
        print(f"[Patched] {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch metadata volume to metadata_json volume in all docker-compose YAML files.")
    parser.add_argument("--dry", action="store_true", help="Print the changes that would be made, but do not write files.")
    args = parser.parse_args()
    files = find_compose_files()
    if not files:
        print("No docker-compose YAML files found in current directory.")
        sys.exit(1)
    for f in files:
        process_file(str(f), dry=args.dry)
    print("Done." if not args.dry else "Dry run complete.")
