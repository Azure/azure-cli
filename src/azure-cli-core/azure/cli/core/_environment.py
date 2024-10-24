# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


_ENV_AZ_INSTALLER = 'AZ_INSTALLER'
_ENV_AZ_BICEP_GLOBALIZATION_INVARIANT = 'AZ_BICEP_GLOBALIZATION_INVARIANT'


def get_config_dir():
    import os
    return os.getenv('AZURE_CONFIG_DIR', None) or os.path.expanduser(os.path.join('~', '.azure'))
