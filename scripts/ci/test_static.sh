#!/usr/bin/env bash

set -ev

export AZDEV_CLI_REPO_PATH=$(pwd)
export AZDEV_EXT_REPO_PATHS='_NONE_'

azdev setup -c $AZDEV_CLI_REPO_PATH
azdev style --pylint
