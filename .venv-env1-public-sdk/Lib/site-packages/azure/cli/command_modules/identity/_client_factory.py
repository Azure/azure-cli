# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _msi_client_factory(cli_ctx, api_version=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_MSI, api_version=api_version)


def _msi_list_resources_client(cli_ctx, **_):
    """
    api version is specified for list resources command because new api version (2023-01-31) of MSI does not support
    listAssociatedResources command. In order to avoid a breaking change, multi-api package is used
    """
    return _msi_client_factory(cli_ctx, api_version='2022-01-31-preview').user_assigned_identities


def _msi_user_identities_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).user_assigned_identities


def _msi_operations_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).operations
