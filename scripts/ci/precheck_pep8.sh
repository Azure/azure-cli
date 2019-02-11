#!/usr/bin/env bash

set -e

export AZDEV_CLI_REPO_PATH=$(pwd)
export AZDEV_EXT_REPO_PATHS='_NONE_'

azdev style --pep8
