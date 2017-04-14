# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#  pylint: disable=unused-import
from azure.cli.core.profiles._shared import (AZURE_API_PROFILES,
                                             ResourceType,
                                             get_api_version as _sdk_get_api_version,
                                             get_versioned_sdk as _sdk_get_versioned_sdk)

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2016-sample': AZURE_API_PROFILES['2016-sample'],
    '2015-sample': AZURE_API_PROFILES['2015-sample']
}


def get_api_version(resource_type):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_api_version(CLOUD.profile, resource_type)


def get_sdk(resource_type, *attr_args, **kwargs):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_versioned_sdk(CLOUD.profile, resource_type, *attr_args, **kwargs)
