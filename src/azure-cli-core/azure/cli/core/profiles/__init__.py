# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#  pylint: disable=unused-import
from azure.cli.core.profiles._shared import AZURE_API_PROFILES, ResourceType

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2017-03-09-profile': AZURE_API_PROFILES['2017-03-09-profile']
}
