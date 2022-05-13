# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import UpdateIntegrationRuntimeNodeRequest


def update(cmd, client, resource_group_name, workspace_name, integration_runtime_name, auto_update,
           update_delay_offset, node_name, no_wait=False):
    update_integration_runtime_node_request = UpdateIntegrationRuntimeNodeRequest(
        auto_update=auto_update,
        update_delay_offset=update_delay_offset
    )
    return sdk_no_wait(no_wait, client.update, resource_group_name, workspace_name, integration_runtime_name,
                       node_name, update_integration_runtime_node_request)
