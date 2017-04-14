# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles.shared import (AZURE_API_PROFILES,
                                            ResourceType,
                                            get_api_version as _sdk_get_api_version,
                                            get_versioned_sdk as _sdk_get_versioned_sdk,
                                            get_versioned_sdk_path as _sdk_get_versioned_sdk_path)

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


def get_versioned_sdk_path(unversioned_path):
    """ Patch the unversioned sdk path to include the appropriate API version for the
        resource type in question.
        e.g. Converts azure.mgmt.storage.operations.storage_accounts_operations to
                      azure.mgmt.storage.v2016_12_01.operations.storage_accounts_operations
    """
    from azure.cli.core._profile import CLOUD
    for rt in ResourceType:
        if unversioned_path.startswith(rt.import_prefix):
            return unversioned_path.replace(rt.import_prefix,
                                            _sdk_get_versioned_sdk_path(CLOUD.profile, rt))
    return unversioned_path
