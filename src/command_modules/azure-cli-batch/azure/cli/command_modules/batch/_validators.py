# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit # pylint: disable=import-error
from datetime import datetime

from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.storage import StorageManagementClient

from azure.cli.core._config import az_config
from azure.cli.core.commands.client_factory import get_mgmt_service_client

# TYPES VALIDATORS

def datetime_type(string):
    """ Validates UTC datetime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. """
    # Here is a bug, need use external libary: isodate, dateutil, etc.
    date_format = '%Y-%m-%dT%H:%MZ'
    return datetime.strptime(string, date_format)

def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)

# COMMAND NAMESPACE VALIDATORS


def validate_required_parameter(ns, parser):
    """Validates required parameters in Batch complex objects"""
    if not parser.done:
        parser.parse(ns)


def storage_account_id(namespace):
    """Validate storage account name"""

    if namespace.storage_account_name:
        if not namespace.storage_account_id:
            storage_client = get_mgmt_service_client(StorageManagementClient)
            acc = storage_client.storage_accounts.get_properties(namespace.resource_group_name,
                                                                 namespace.storage_account_name)
            if not acc:
                raise ValueError("Batch account '{}' not found in the resource group '{}'.". \
                    format(namespace.storage_account_name, namespace.resource_group_name))
            namespace.storage_account_id = acc.id #pylint: disable=no-member
    del namespace.storage_account_name

def application_enabled(namespace):
    """Validates account has auto-storage enabled"""

    client = get_mgmt_service_client(BatchManagementClient)
    acc = client.batch_account.get(namespace.resource_group_name, namespace.account_name)
    if not acc:
        raise ValueError("Batch account '{}' not found.".format(namespace.account_name))
    if not acc.auto_storage or not acc.auto_storage.storage_account_id: #pylint: disable=no-member
        raise ValueError("Batch account '{}' needs auto-storage enabled.".
                         format(namespace.account_name))

def validate_client_parameters(namespace):
    """Retrieves Batch connection parameters from environment variables"""

    # simply try to retrieve the remaining variables from environment variables
    if not namespace.account_name:
        namespace.account_name = az_config.get('batch', 'account', None)
    if not namespace.account_key:
        namespace.account_key = az_config.get('batch', 'access_key', None)
    if not namespace.account_endpoint:
        namespace.account_endpoint = az_config.get('batch', 'endpoint', None)

    # if account name is specified but no key, attempt to query
    if namespace.account_name and namespace.account_endpoint and not namespace.account_key:
        endpoint = urlsplit(namespace.account_endpoint)
        host = endpoint.netloc
        client = get_mgmt_service_client(BatchManagementClient)
        acc = next((x for x in client.batch_account.list() \
            if x.name == namespace.account_name and x.account_endpoint == host), None)
        if acc:
            from azure.cli.core.commands.arm import parse_resource_id
            rg = parse_resource_id(acc.id)['resource_group']
            namespace.account_key = \
                client.batch_account.get_keys(rg, namespace.account_name).primary #pylint: disable=no-member
        else:
            raise ValueError("Batch account '{}' not found.".format(namespace.account_name))
    else:
        if not namespace.account_name:
            raise ValueError("Need specifiy batch account in command line or enviroment variable.")
        if not namespace.account_endpoint:
            raise ValueError("Need specifiy batch endpoint in command line or enviroment variable.")
