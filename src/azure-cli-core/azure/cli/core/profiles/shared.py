# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO Move this to a package shared by CLI and SDK

from importlib import import_module
from enum import Enum


class APIVersionException(Exception):
    def __init__(self, type_name, api_profile):
        super(APIVersionException, self).__init__(type_name, api_profile)
        self.type_name = type_name
        self.api_profile = api_profile

    def __str__(self):
        return "Unable to get API version for type '{}' in profile '{}'".format(
            self.type_name, self.api_profile)


class ResourceType(Enum):  # pylint: disable=too-few-public-methods

    MGMT_STORAGE_STORAGE_ACCOUNTS = ('Microsoft.Storage/storageAccounts',
                                     'azure.mgmt.storage',
                                     'StorageManagementClient')

    def __init__(self, type_name, sdk_module, client_name):
        """Constructor.

        :param type_name: The full resource type name (e.g. Provider/ResourceType).
        :type type_name: str.
        :param sdk_module: Path to the sdk module.
        :type sdk_module: str.
        :param client_name: The name of the client for this resource type.
        :type client_name: str.
        """
        self.type_name = type_name
        self.sdk_module = sdk_module
        self.client_name = client_name


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
    """Get the API version of a resource type given an API profile.

    :param api_profile: The name of the API profile.
    :type api_profile: str.
    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :returns:  str -- the API version.
    :raises: APIVersionException
    """
    try:
        return AZURE_API_PROFILES[api_profile][resource_type]
    except KeyError:
        raise APIVersionException(resource_type.type_name, api_profile)


def get_client_class(resource_type):
    """Get the uninstantiated Client class for this resource type.

    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :raises: ImportError, AttributeError
    :returns:  class -- the Client class.
    """
    return getattr(import_module(resource_type.sdk_module), resource_type.client_name)


def get_versioned_models(api_profile, resource_type, *model_args, **kwargs):
    """Get the models for a given resource type and version.

    :param api_profile: The name of the API profile.
    :type api_profile: str.
    :param resource_type: The resource type.
    :type resource_type: ResourceType.
    :param model_args: Arguments for the models to be returned
    :type model_args: str.
    :param checked: If True, import exceptions are caught and None is returned, otherwise exception.
    :type checked: bool.
    :returns:  List of models if multiple specified, otherwise the model
    """
    checked = kwargs.get('checked', True)
    api_version = get_api_version(api_profile, resource_type)
    try:
        models_mod = get_client_class(resource_type).models(api_version=api_version)
        models = []
        for m in model_args:
            new_model = getattr(models_mod, m, None) if checked else getattr(models_mod, m)
            models.append(new_model)
        return models[0] if len(models) == 1 else models
    except (ImportError, AttributeError) as ex:
        if checked:
            return None
        raise ex
