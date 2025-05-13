#!/bin/bash

# Check if in the python environment
PYTHON_FILE=$(which python)
printf "PYTHON_PATH: %s\n" "$PYTHON_FILE"

if [ -z "$PYTHON_FILE" ]; then
    printf "\033[0;31mError: Python not found in PATH\033[0m\n"
    exit 1
fi

PYTHON_ENV_FOLDER=$(dirname "$PYTHON_FILE")
PYTHON_ACTIVE_FILE="$PYTHON_ENV_FOLDER/activate"

if [ ! -f "$PYTHON_ACTIVE_FILE" ]; then
    printf "Python active file does not exist: %s\n" "$PYTHON_ACTIVE_FILE"
    printf "\033[0;31mError: Please activate the python environment first.\033[0m\n"
    exit 1
fi

# Construct the full path to the .azdev/env_config directory
AZDEV_ENV_CONFIG_FOLDER="$HOME/.azdev/env_config"
printf "AZDEV_ENV_CONFIG_FOLDER: %s\n" "$AZDEV_ENV_CONFIG_FOLDER"

# Check if the directory exists
if [ ! -d "$AZDEV_ENV_CONFIG_FOLDER" ]; then
    printf "AZDEV_ENV_CONFIG_FOLDER does not exist: %s\n" "$AZDEV_ENV_CONFIG_FOLDER"
    printf "\033[0;31mError: azdev environment is not completed, please run 'azdev setup' first.\033[0m\n"
    exit 1
fi

PYTHON_ENV_FOLDER=$(dirname "$PYTHON_ENV_FOLDER")

CONFIG_FILE="$AZDEV_ENV_CONFIG_FOLDER${PYTHON_ENV_FOLDER}/config"
if [ ! -f "$CONFIG_FILE" ]; then
    printf "CONFIG_FILE does not exist: %s\n" "$CONFIG_FILE"
    printf "\033[0;31mError: azdev environment is not completed, please run 'azdev setup' first.\033[0m\n"
    exit 1
fi

printf "CONFIG_FILE: %s\n" "$CONFIG_FILE"
