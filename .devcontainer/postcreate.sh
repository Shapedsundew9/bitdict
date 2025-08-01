#!/bin/bash

# This script runs after the container is created.
# The 'set -e' command ensures that the script will exit immediately if a command fails.
set -e

echo "--- Running post-create script ---"

# Activating the virtual environment
echo "Creating virtual environment..."
python3 -m venv /workspaces/.venv

# Install Python dependencies from requirements.txt
echo "Installing requirements..."
/workspaces/.venv/bin/pip install --upgrade pip
/workspaces/.venv/bin/pip install pre-commit
find . -name "requirements.txt" -exec /workspaces/.venv/bin/pip install -r {} \;

# Done
echo "--- Post-create script finished ---"