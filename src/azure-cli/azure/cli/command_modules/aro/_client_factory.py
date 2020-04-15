# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.redhatopenshift import AzureRedHatOpenShiftClient


def cf_aro(cli_ctx, *_):
    client = get_mgmt_service_client(
        cli_ctx, AzureRedHatOpenShiftClient).open_shift_clusters

    return client
