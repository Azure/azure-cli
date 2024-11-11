#!/bin/bash

# Check if in the python environment
PYTHON_FILE=$(which python)
echo "PYTHON_PATH: $PYTHON_FILE"

if [ -z "$PYTHON_FILE" ]; then
    echo "\033[0;31mError: Python not found in PATH\033[0m"
    exit 1
fi

PYTHON_ENV_FOLDER=$(dirname "$PYTHON_FILE")
PYTHON_ACTIVE_FILE="$PYTHON_ENV_FOLDER/activate"

if [ ! -f "$PYTHON_ACTIVE_FILE" ]; then
    echo "Python active file does not exist: $PYTHON_ACTIVE_FILE"
    echo "\033[0;31mError: Please activate the python environment first.\033[0m"
    exit 1
fi

# Construct the full path to the .azdev/env_config directory
AZDEV_ENV_CONFIG_FOLDER="$HOME/.azdev/env_config"
echo "AZDEV_ENV_CONFIG_FOLDER: $AZDEV_ENV_CONFIG_FOLDER"

# Check if the directory exists
if [ ! -d "$AZDEV_ENV_CONFIG_FOLDER" ]; then
    echo "AZDEV_ENV_CONFIG_FOLDER does not exist: $AZDEV_ENV_CONFIG_FOLDER"
    echo "\033[0;31mError: azdev environment is not completed, please run 'azdev setup' first.\033[0m"
    exit 1
fi

PYTHON_ENV_FOLDER=$(dirname "$PYTHON_ENV_FOLDER")

CONFIG_FILE="$AZDEV_ENV_CONFIG_FOLDER${PYTHON_ENV_FOLDER}/config"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "CONFIG_FILE does not exist: $CONFIG_FILE"
    echo "\033[0;31mError: azdev environment is not completed, please run 'azdev setup' first.\033[0m"
    exit 1
fi

echo "CONFIG_FILE: $CONFIG_FILE"