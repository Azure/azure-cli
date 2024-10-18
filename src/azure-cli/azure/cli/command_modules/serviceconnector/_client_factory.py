# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_connection_cl(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.servicelinker import ServiceLinkerManagementClient

    return get_mgmt_service_client(cli_ctx, ServiceLinkerManagementClient,
                                   subscription_bound=False, api_version="2024-07-01-preview")


def cf_linker(cli_ctx, *_):
    return cf_connection_cl(cli_ctx).linker


def cf_connector(cli_ctx, *_):
    return cf_connection_cl(cli_ctx).connector


def cf_configuration_names(cli_ctx, *_):
    return cf_connection_cl(cli_ctx).configuration_names
