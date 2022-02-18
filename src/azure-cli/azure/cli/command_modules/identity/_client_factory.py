# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _msi_client_factory(cli_ctx, **_):
    from azure.mgmt.msi import ManagedServiceIdentityClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ManagedServiceIdentityClient)


def _msi_user_identities_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).user_assigned_identities


def _msi_operations_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).operations
