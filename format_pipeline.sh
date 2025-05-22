#!/bin/bash
# Auto-format all core pipeline Python files using black

# Fail on error
set -e

# Ensure black is installed (locally or via pipx)
if ! command -v black &> /dev/null
then
    echo "Installing black..."
    pip install black
fi

echo "Auto-formatting pipeline Python files..."
# Format all .py files in the core service directories and shared
black watcher/ metadata/ splitter/ packager/ organizer/ status-api/ maintenance/ telegram_youtube_bot/ shared/

echo "Formatting complete!"
