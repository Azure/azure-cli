#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

export PYTHONPATH=${PYTHONPATH}:$(cd $(dirname $0); pwd)
python -m automation.coverage.run
