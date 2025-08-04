#!/bin/bash

# This script sets up a pre-push hook for a Python project in a development container.
# It installs necessary Python dependencies and configures the pre-push hook to run linting and
# type checks before allowing a push to proceed.
#
# NOTE: Pre-Push hooks will *NOT* be run if the last commit message starts with "WIP:".

# Exit immediately if a command exits with a non-zero status.
set -e

# Assumes the script is run in the context of a dev container workspace folder.
echo "Installing Pre-Push Hook Python dependencies..."

# Use a common command that works in all environments
.venv/bin/pip install -r requirements-dev.txt

echo "Installing pre-push hooks..."
.venv/bin/pre-commit install --install-hooks
.venv/bin/pre-commit install --hook-type pre-push

echo "Creating conditional pre-push hook..."

HOOK_PATH=".git/hooks/pre-push"

# Backup the default pre-push hook if it exists
if [ -f "$HOOK_PATH" ]; then
  mv "$HOOK_PATH" "$HOOK_PATH.bak"
fi

# Create the new pre-push hook with conditional logic
cat > "$HOOK_PATH" << EOF
#!/bin/bash

echo "Pre-push hook is running from: \$(pwd)"

# Universal check for dev container environment, works in Codespaces and local containers.
if [ -z "\$CODESPACES" ] && [ -z "\$VSCODE_DEVCONTAINER_SESSION_ID" ]; then
  echo "Not in a Codespace or Dev Container. Skipping pre-push checks."
  # Add a specific message to prompt the user to install hooks
  echo "Please run 'pre-commit install --hook-type pre-push' if you want these checks."
  exit 0
fi

# Get the last commit message
last_commit_message=\$(git log -1 --pretty=%B)

# Condition to skip checks
if [[ "\$last_commit_message" == WIP:* ]]; then
  echo "Commit message starts with 'WIP:'. Skipping linting and type checks."
  exit 0
fi

echo "Running pre-push hooks (pylint & pyright)..."

.venv/bin/pre-commit run --hook-id black --verbose
.venv/bin/pre-commit run --hook-id isort --verbose
.venv/bin/pre-commit run --hook-id pylint --verbose
.venv/bin/pre-commit run --hook-id pyright --verbose

if [ \$? -ne 0 ]; then
  echo "Pre-push checks failed. Push aborted."
  exit 1
fi

echo "All checks passed. Push commencing."
exit 0
EOF

chmod +x "$HOOK_PATH"

echo "Pre-Push Hook Setup complete!"
