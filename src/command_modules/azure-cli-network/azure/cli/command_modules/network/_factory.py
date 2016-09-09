#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.network import NetworkManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client

def _network_client_factory(**_):
    return get_mgmt_service_client(NetworkManagementClient)
