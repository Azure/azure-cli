# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.batch import BatchManagementClient

import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth

from azure.cli.core.commands.client_factory import get_mgmt_service_client

def batch_client_factory(**_):
    return get_mgmt_service_client(BatchManagementClient)

def batch_data_service_factory(**kwargs):
    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    account_endpoint = kwargs.pop('account_endpoint', None)
    credentials = batchauth.SharedKeyCredentials(account_name, account_key)
    return batch.BatchServiceClient(credentials, base_url=account_endpoint)
