# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, too-many-statements, too-many-locals
from azure.cli.core.util import sdk_no_wait
from .._client_factory import cf_synapse_managedprivateendpoints_factory
from azure.synapse.managedprivateendpoints.models import ManagedPrivateEndpointProperties


def create_Managed_private_endpoints(cmd, workspace_name, managed_private_endpoint_name, definition_file, no_wait=False):
    client = cf_synapse_managedprivateendpoints_factory(cmd.cli_ctx, workspace_name)
    properties = ManagedPrivateEndpointProperties.from_dict(definition_file)
    managed_virtual_network_name = "default"
    return sdk_no_wait(no_wait, client.create,
                       managed_private_endpoint_name, managed_virtual_network_name, properties)


def get_Managed_private_endpoints(cmd, workspace_name, managed_private_endpoint_name):
    client = cf_synapse_managedprivateendpoints_factory(cmd.cli_ctx, workspace_name)
    managed_virtual_network_name = "default"
    return client.get(managed_private_endpoint_name, managed_virtual_network_name)


def list_Managed_private_endpoints(cmd, workspace_name):
    client = cf_synapse_managedprivateendpoints_factory(cmd.cli_ctx, workspace_name)
    managed_virtual_network_name = "default"
    return client.list(managed_virtual_network_name)


def delete_Managed_private_endpoints(cmd, workspace_name, managed_private_endpoint_name, no_wait=False):
    client = cf_synapse_managedprivateendpoints_factory(cmd.cli_ctx, workspace_name)
    managed_virtual_network_name = "default"
    return sdk_no_wait(no_wait, client.delete, managed_private_endpoint_name, managed_virtual_network_name)
