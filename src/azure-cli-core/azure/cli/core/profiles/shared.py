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

    # TODO Thinking of removing the RP/RT format due to swagger/sdk format
    MGMT_STORAGE = ('Microsoft.Storage/storageAccounts',
                    'azure.mgmt.storage',
                    'azure.mgmt.storage#StorageManagementClient')
    MGMT_COMPUTE = ('Microsoft.Compute/all',
                    'azure.mgmt.compute.compute',
                    'azure.mgmt.compute#ComputeManagementClient')
    MGMT_CONTAINER_SERVICE = ('Microsoft.ContainerService/all',
                              'azure.mgmt.compute.containerservice',
                              'azure.mgmt.compute#ContainerServiceClient')
    MGMT_NETWORK = ('Microsoft.Network/all',
                    'azure.mgmt.network',
                    'azure.mgmt.network#NetworkManagementClient')
    MGMT_RESOURCE_FEATURES = ('Microsoft.Features/features',
                              'azure.mgmt.resource.features',
                              'azure.mgmt.resource#FeatureClient')
    MGMT_RESOURCE_LINKS = ('Microsoft.Resources/links',
                           'azure.mgmt.resource.links',
                           'azure.mgmt.resource#ManagementLinkClient')
    MGMT_RESOURCE_LOCKS = ('Microsoft.Authorization/locks',
                           'azure.mgmt.resource.locks',
                           'azure.mgmt.resource#ManagementLockClient')
    MGMT_RESOURCE_POLICY = ('Microsoft.Authorization/policyassignments',
                            'azure.mgmt.resource.policy',
                            'azure.mgmt.resource#PolicyClient')
    MGMT_RESOURCE_RESOURCES = ('Microsoft.Resources/deployments',
                               'azure.mgmt.resource.resources',
                               'azure.mgmt.resource#ResourceManagementClient')
    MGMT_RESOURCE_SUBSCRIPTIONS = ('Microsoft.Resources/subscriptions',
                                   'azure.mgmt.resource.subscriptions',
                                   'azure.mgmt.resource#SubscriptionClient')

    def __init__(self, type_name, operations_path, client_path):
        """Constructor.

        :param type_name: The full resource type name (e.g. Provider/ResourceType).
        :type type_name: str.
        :param operations_path: Path to the (unversioned) operations module.
        :type operations_path: str.
        :param client_path: The path to the client for this resource type.
        :type client_path: str.
        """
        self.type_name = type_name
        self.operations_path = operations_path
        self.client_path = client_path


AZURE_API_PROFILES = {
    'latest': {
        ResourceType.MGMT_STORAGE: '2016-12-01',
        ResourceType.MGMT_NETWORK: '2016-09-01',
        ResourceType.MGMT_CONTAINER_SERVICE: '2017-01-31',
        ResourceType.MGMT_COMPUTE: '2016-04-30-preview',
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-04-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2016-09-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01'
    },
    '2016-example': {
        ResourceType.MGMT_STORAGE: '2016-12-01',
        ResourceType.MGMT_NETWORK: '2016-09-01',
        ResourceType.MGMT_CONTAINER_SERVICE: '2017-01-31',
        ResourceType.MGMT_COMPUTE: '2016-04-30-preview',
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-12-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2016-09-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01'
    },
    '2015-example': {
        ResourceType.MGMT_STORAGE: '2015-06-15',
        ResourceType.MGMT_NETWORK: '2015-06-15',
        ResourceType.MGMT_CONTAINER_SERVICE: '2017-01-31',
        ResourceType.MGMT_COMPUTE: '2015-06-15',
        ResourceType.MGMT_RESOURCE_FEATURES: '2015-12-01',
        ResourceType.MGMT_RESOURCE_LINKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_LOCKS: '2016-09-01',
        ResourceType.MGMT_RESOURCE_POLICY: '2016-12-01',
        ResourceType.MGMT_RESOURCE_RESOURCES: '2016-09-01',
        ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS: '2016-06-01'
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
    :returns:  class -- the Client class.
    """
    cp = resource_type.client_path
    mod_to_import, attr_path = cp.split('#')
    op = import_module(mod_to_import)
    for part in attr_path.split('.'):
        op = getattr(op, part)
    return op


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
