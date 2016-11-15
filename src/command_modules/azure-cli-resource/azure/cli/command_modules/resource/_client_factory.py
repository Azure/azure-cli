# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def _resource_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    return get_mgmt_service_client(ResourceManagementClient)

def _resource_feature_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.features  import FeatureClient
    return get_mgmt_service_client(FeatureClient)

def _resource_policy_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.policy import PolicyClient
    return get_mgmt_service_client(PolicyClient)

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

