# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK

from importlib import import_module
from enum import Enum


class APIVersionException(Exception):
    # API Version is not available for API profile or resource type.
    pass


class ResourceType(Enum):  # pylint: disable=too-few-public-methods
    def __init__(self, type_name, sdk_module, client_name):
        self.type_name = type_name
        self.sdk_module = sdk_module
        self.client_name = client_name

    MGMT_STORAGE_STORAGE_ACCOUNTS = ('Microsoft.Storage/storageAccounts',
                                     'azure.mgmt.storage',
                                     'StorageManagementClient')


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS: '2016-12-01'
    },
    '2016-example': {
        ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS: '2016-12-01'
    },
    '2015-example': {
        ResourceType.MGMT_STORAGE_STORAGE_ACCOUNTS: '2015-06-15'
    }
}


def get_api_version(api_profile, resource_type):
    try:
        return AZURE_API_PROFILES[api_profile][resource_type]
    except KeyError:
        raise APIVersionException("Unable to get API version for type '{}' in profile '{}'".format(
            resource_type.type_name, api_profile))


def get_client_class(resource_type):
    return getattr(import_module(resource_type.sdk_module), resource_type.client_name)


def get_versioned_models(api_profile, resource_type, model=None, checked=True):
    api_version = get_api_version(api_profile, resource_type)
    try:
        models = get_client_class(resource_type).models(api_version=api_version)
        return getattr(models, model) if model else models
    except (ImportError, AttributeError) as ex:
        if checked:
            return None
        raise ex
