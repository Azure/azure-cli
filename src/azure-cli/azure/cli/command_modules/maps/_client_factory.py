# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_maps(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.maps import MapsManagementClient
    return get_mgmt_service_client(cli_ctx, MapsManagementClient)


def cf_accounts(cli_ctx, *_):
    return cf_maps(cli_ctx).accounts
