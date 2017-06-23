# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.sf.config import SfConfigParser
from azure.cli.core.util import CLIError
from azure.servicefabric import ServiceFabricClientAPIs
from azure.cli.command_modules.sf.cluster_auth import ClientCertAuthentication
from azure.cli.core.commands.client_factory import configure_common_settings


def cf_sf_client(_):
    sf_config = SfConfigParser()
    endpoint = sf_config.connection_endpoint()
    if not endpoint:
        raise CLIError("Connection endpoint not specified, run 'az sf cluster select' first.")

    cert = sf_config.cert_info()
    ca_cert = sf_config.ca_cert_info()
    no_verify = sf_config.no_verify_setting()

    auth = ClientCertAuthentication(cert, ca_cert, no_verify)
    client = ServiceFabricClientAPIs(auth, base_url=endpoint)
    configure_common_settings(client)
    return client
