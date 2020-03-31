# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import urllib3

from azure.cli.command_modules.aro.custom import rp_mode_development
from azure.cli.command_modules.aro.vendored_sdks.azure.mgmt.redhatopenshift.v2020_04_30 import AzureRedHatOpenShiftClient #pylint: disable=line-too-long
from azure.cli.core.commands.client_factory import get_mgmt_service_client


def cf_aro(cli_ctx, *_):
    client = get_mgmt_service_client(
        cli_ctx, AzureRedHatOpenShiftClient).open_shift_clusters

    if rp_mode_development():
        client.config.base_url = 'https://localhost:8443/'
        client.config.connection.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return client
