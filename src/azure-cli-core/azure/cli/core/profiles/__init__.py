# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles.shared import (AZURE_API_PROFILES,
                                            get_api_version as _sdk_get_api_version,
                                            get_versioned_models as _sdk_get_versioned_models)

# API Profiles currently supported in the CLI.
API_PROFILES = {
    'latest': AZURE_API_PROFILES['latest'],
    '2016-example': AZURE_API_PROFILES['2016-example'],
    '2015-example': AZURE_API_PROFILES['2015-example']
}


def get_api_version(resource_type):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_api_version(CLOUD.profile, resource_type)


def get_versioned_models(resource_type, *model_args, **kwargs):
    from azure.cli.core._profile import CLOUD
    return _sdk_get_versioned_models(CLOUD.profile, resource_type, *model_args, **kwargs)
