#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.features  import FeatureClient
from azure.mgmt.resource.policy import PolicyClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client

def _resource_client_factory(**_):
    return get_mgmt_service_client(ResourceManagementClient)

def _resource_feature_client_factory(**_):
    return get_mgmt_service_client(FeatureClient)

def _resource_policy_client_factory(**_):
    return get_mgmt_service_client(PolicyClient)
