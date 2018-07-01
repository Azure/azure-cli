# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_relay(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.relay import RelayManagementClient
    return get_mgmt_service_client(cli_ctx, RelayManagementClient)


def namespaces_mgmt_client_factory(cli_ctx, _):
    return cf_relay(cli_ctx).namespaces


def wcfrelays_mgmt_client_factory(cli_ctx, _):
    return cf_relay(cli_ctx).wcf_relays


def hycos_mgmt_client_factory(cli_ctx, _):
    return cf_relay(cli_ctx).hybrid_connections
