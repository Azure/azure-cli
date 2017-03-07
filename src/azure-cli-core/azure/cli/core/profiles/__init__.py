# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles._shared import AZURE_API_PROFILES

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': {},
    '2016-01-01-example': AZURE_API_PROFILES['2016-01-01-example'],
    '2015-06-15-example': AZURE_API_PROFILES['2015-06-15-example']
}
