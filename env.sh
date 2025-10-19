#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Please use 'source $(basename "$0")'"
    exit 1
fi

TARGET_DIR="${1:-$(pwd)}"

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: Target directory '$TARGET_DIR' does not exist."
    return 1
fi

if [[ "$(uname)" != "Darwin" ]] && ! (python3 -m venv --help &>/dev/null); then
    echo "Installing python3-venv..."
    sudo apt update && sudo apt install -y python3-venv
fi

if [[ ! -d "$TARGET_DIR/env/" ]]; then
    echo "Creating virtual environment in $TARGET_DIR/env/ ..."
    python3 -m venv "$TARGET_DIR/env/"
fi

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment from $TARGET_DIR/env/ ..."
    source "$TARGET_DIR/env/bin/activate"
fi

if [[ -f "$TARGET_DIR/requirements.txt" ]]; then
    echo "Installing requirements from $TARGET_DIR/requirements.txt ..."
    # no internet halts next 2 lines
    pip install --upgrade pip
    pip install --upgrade -r "$TARGET_DIR/requirements.txt"
fi
