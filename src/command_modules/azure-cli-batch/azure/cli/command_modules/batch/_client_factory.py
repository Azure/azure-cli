# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.batch import BatchManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client

def batch_client_factory(**_):
    return get_mgmt_service_client(BatchManagementClient)
