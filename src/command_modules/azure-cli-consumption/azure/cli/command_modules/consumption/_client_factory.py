# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_consumption(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.consumption import ConsumptionManagementClient
    return get_mgmt_service_client(cli_ctx, ConsumptionManagementClient)


def usage_details_mgmt_client_factory(cli_ctx, kwargs):
    return cf_consumption(cli_ctx, **kwargs).usage_details
