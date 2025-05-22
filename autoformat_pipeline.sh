#!/bin/bash

# Auto-format, lint-fix, and clean up all pipeline code (Black + autoflake)
# Ensure you have black and autoflake installed
pip install --upgrade black autoflake

echo "Running autoflake to remove unused imports/variables..."
autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r \
  watcher/ metadata/ splitter/ packager/ organizer/ status-api/ maintenance/ telegram_youtube_bot/ shared/

echo "Running Black for code formatting..."
black watcher/ metadata/ splitter/ packager/ organizer/ status-api/ maintenance/ telegram_youtube_bot/ shared/

echo "All pipeline services auto-formatted and linted!"

echo "Tip: Review the output with git diff, then commit and push."
