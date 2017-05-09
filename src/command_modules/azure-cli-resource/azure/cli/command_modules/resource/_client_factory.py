# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _resource_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)


def _resource_feature_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_FEATURES)


def _resource_policy_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_POLICY)


def _resource_lock_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_LOCKS)


def _resource_links_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_LINKS)


def _authorization_management_client(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.authorization import AuthorizationManagementClient
    return get_mgmt_service_client(AuthorizationManagementClient)


def _resource_managedapps_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.managedapplications import ManagedApplicationClient
    return get_mgmt_service_client(ManagedApplicationClient)


def cf_resource_groups(_):
    return _resource_client_factory().resource_groups


def cf_resources(_):
    return _resource_client_factory().resources


def cf_providers(_):
    return _resource_client_factory().providers


def cf_tags(_):
    return _resource_client_factory().tags


def cf_deployments(_):
    return _resource_client_factory().deployments


def cf_deployment_operations(_):
    return _resource_client_factory().deployment_operations


def cf_features(_):
    return _resource_feature_client_factory().features


def cf_policy_definitions(_):
    return _resource_policy_client_factory().policy_definitions


def cf_management_locks(_):
    return _resource_lock_client_factory().management_locks


def cf_resource_links():
    return _resource_links_client_factory().resource_links


def cf_resource_managedapplications(_):
    return _resource_managedapps_client_factory().appliances


def cf_resource_managedappdefinitions(_):
    return _resource_managedapps_client_factory().appliance_definitions
