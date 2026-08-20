# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.redhatopenshift import AzureRedHatOpenShiftClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client


def cf_aro(cli_ctx, *_):
    opt_args = {}

    client = get_mgmt_service_client(
        cli_ctx, AzureRedHatOpenShiftClient, base_url_bound=False, **opt_args)

    return client
