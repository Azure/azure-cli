# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def list_identity_resources(cmd, resource_group_name, resource_name):
    from azure.cli.command_modules.identity._client_factory import _msi_list_resources_client
    client = _msi_list_resources_client(cmd.cli_ctx)
    return client.list_associated_resources(resource_group_name=resource_group_name,
                                            resource_name=resource_name)
