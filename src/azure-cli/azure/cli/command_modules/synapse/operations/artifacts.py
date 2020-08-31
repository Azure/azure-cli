# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.synapse.artifacts.models import LinkedService
from azure.cli.core.util import sdk_no_wait
from .._client_factory import cf_synapse_linked_service


# Linked Service
def list_linked_service(cmd, workspace_name):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return client.get_linked_services_by_workspace()


def get_linked_service(cmd, workspace_name, linked_service_name):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return client.get_linked_service(linked_service_name)


def create_or_update_linked_service(cmd, workspace_name, linked_service_name, definition_file, no_wait=False):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    properties = LinkedService.from_dict(definition_file['properties'])
    return sdk_no_wait(no_wait, client.begin_create_or_update_linked_service,
                       linked_service_name, properties, polling=True)


def delete_linked_service(cmd, workspace_name, linked_service_name, no_wait=False):
    client = cf_synapse_linked_service(cmd.cli_ctx, workspace_name)
    return sdk_no_wait(no_wait, client.begin_delete_linked_service, linked_service_name, polling=True)
