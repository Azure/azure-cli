# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import urllib3

from azext_aro.custom import rp_mode_development
from azext_aro.vendored_sdks.azure.mgmt.redhatopenshift import AzureRedHatOpenShiftClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client


def cf_aro(cli_ctx, *_):

    opt_args = {}

    if rp_mode_development():
        opt_args = {
            "base_url": "https://localhost:8443/",
            "connection_verify": False
        }
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    client = get_mgmt_service_client(
        cli_ctx, AzureRedHatOpenShiftClient, base_url_bound=False, **opt_args)

    return client
