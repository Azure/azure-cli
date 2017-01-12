# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


def get_config_dir():
    if os.getenv('AZURE_CONFIG_DIR'):
        return os.getenv('AZURE_CONFIG_DIR')
    else:
        return os.path.expanduser(os.path.join('~', '.azure'))
