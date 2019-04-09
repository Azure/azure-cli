# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_privatedns_mgmt_zones(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient).private_zones


def cf_privatedns_mgmt_virtual_network_links(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient).virtual_network_links


def cf_privatedns_mgmt_record_sets(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.privatedns import PrivateDnsManagementClient
    return get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient).record_sets
