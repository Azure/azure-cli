# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core._environment import get_config_dir

GLOBAL_CONFIG_DIR = get_config_dir()
CONFIG_FILE_NAME = 'config'
SURVEY_NOTE_NAME = 'survey.json'
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, CONFIG_FILE_NAME)
GLOBAL_SURVEY_NOTE_PATH = os.path.join(GLOBAL_CONFIG_DIR, SURVEY_NOTE_NAME)
ENV_VAR_PREFIX = 'AZURE'
