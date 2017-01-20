# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit # pylint: disable=import-error

from msrest.serialization import Deserializer
from msrest.exceptions import DeserializationError

from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.storage import StorageManagementClient

from azure.cli.core._config import az_config
from azure.cli.core.commands.client_factory import get_mgmt_service_client

# TYPES VALIDATORS

def datetime_type(string):
    """ Validates UTC datetime in format '%Y-%m-%d\'T\'%H:%M\'Z\''. """
    try:
        date_obj = Deserializer.deserialize_iso(string)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(string))
    else:
        return date_obj


def validate_datetime(namespace, name, parser):
    """Validate the correct format of a datetime string and deserialize."""
    date_str = getattr(namespace, name)
    if date_str and isinstance(date_str, str):
        try:
            date_obj = Deserializer.deserialize_iso(date_str)
        except DeserializationError:
            message = "Argument {} is not a valid ISO-8601 datetime format"
            raise ValueError(message.format(name))
        else:
            setattr(namespace, name, date_obj)
    validate_required_parameter(namespace, parser)


def validate_duration(name, value):
    """Validate the correct format of a timespan string and deserilize."""
    try:
        value = Deserializer.deserialize_duration(value)
    except DeserializationError:
        message = "Argument {} is not in a valid ISO-8601 duration format"
        raise ValueError(message.format(name))
    else:
        return value


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


def validate_options(namespace):
    """Validate any flattened request header option arguments."""
    try:
        start = namespace.start_range
        end = namespace.end_range
    except AttributeError:
        pass
    else:
        namespace.ocp_range = None
        del namespace.start_range
        del namespace.end_range
        if start or end:
            start = start if start else 0
            end = end if end else ""
            namespace.ocp_range = "bytes={}-{}".format(start, end)
    # TODO: Should we also try RFC-1123?
    for date_arg in ['if_modified_since', 'if_unmodified_since']:
        try:
            date_str = getattr(namespace, date_arg)
            if date_str and isinstance(date_str, str):
                date_obj = Deserializer.deserialize_iso(date_str)
        except AttributeError:
            pass
        except DeserializationError:
            message = "Argument {} is not a valid ISO-8601 datetime format"
            raise ValueError(message.format(date_arg))
        else:
            setattr(namespace, date_arg, date_obj)


def validate_file_destination(namespace):
    """Validate the destination path for a file download."""
    try:
        path = namespace.destination
    except AttributeError:
        return
    else:
        # TODO: Need to confirm this logic...
        file_path = path
        file_dir = os.path.dirname(path)
        if os.path.isdir(path):
            file_name = os.path.basename(namespace.file_name)
            file_path = os.path.join(path, file_name)
        elif not os.path.isdir(file_dir):
            try:
                os.mkdir(file_dir)
            except EnvironmentError as exp:
                raise ValueError("Directory {} does not exist, and cannot be created: {}".\
                    format(file_dir, exp))
        if os.path.isfile(file_path):
            raise ValueError("File {} already exists.".format(file_path))
        namespace.destination = file_path


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

# CUSTOM REQUEST VALIDATORS

def validate_pool_settings(namespace, parser):
    """Custom parsing to enfore that either PaaS or IaaS instances are configured
    in the add pool request body.
    """
    groups = ['pool.cloud_service_configuration', 'pool.virtual_machine_configuration']
    parser.parse_mutually_exclusive(namespace, True, groups)
