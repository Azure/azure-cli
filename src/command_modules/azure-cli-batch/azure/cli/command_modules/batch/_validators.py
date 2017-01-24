# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
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


def datetime_format(value):
    """Validate the correct format of a datetime string and deserialize."""
    try:
        datetime_obj = Deserializer.deserialize_iso(value)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(value))
    else:
        return datetime_obj


def duration_format(value):
    """Validate the correct format of a timespan string and deserilize."""
    try:
        duration_obj = Deserializer.deserialize_duration(value)
    except DeserializationError:
        message = "Argument {} is not in a valid ISO-8601 duration format"
        raise ValueError(message.format(value))
    else:
        return duration_obj


def metadata_item_format(value):
    """Validate listed metadata arguments"""
    try:
        data_name, data_value = value.split('=')
    except ValueError:
        message = ("Incorrectly formatted metadata. "
                   "Argmuent values should be in the format a=b c=d")
        raise ValueError(message)
    else:
        return {'name': data_name, 'value': data_value}


def environment_setting_format(value):
    """Validate listed enviroment settings arguments"""
    try:
        env_name, env_value = value.split('=')
    except ValueError:
        message = ("Incorrectly formatted enviroment settings. "
                   "Argmuent values should be in the format a=b c=d")
        raise ValueError(message)
    else:
        return {'name': env_name, 'value': env_value}


def application_package_reference_format(value):
    """Validate listed application package reference arguments"""
    app_reference = value.split('#', 1)
    package = {'application_id': app_reference[0]}
    try:
        package['version'] = app_reference[1]
    except IndexError:  # No specified version - ignore
        pass
    return package


def certificate_reference_format(value):
    """Validate listed certificate reference arguments"""
    cert = {'thumbprint': value, 'thumbprint_algorithm': 'sha1'}
    return cert


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


def validate_pool_resize_parameters(namespace):
    """Validate pool resize parameters correct"""
    if not namespace.abort:
        if not namespace.target_dedicated:
            raise ValueError("The target-dedicated parameter is required to resize the pool.")


def validate_json_file(namespace):
    """Validate the give json file existing"""
    if namespace.json_file:
        try:
            with open(namespace.json_file) as file_handle:
                json.load(file_handle)
        except EnvironmentError:
            raise ValueError("Cannot access JSON request file: " + namespace.json_file)
        except ValueError as err:
            raise ValueError("Invalid JSON file: {}".format(err))


def validate_cert_file(namespace):
    """Validate the give cert file existing"""
    try:
        with open(namespace.cert_file, "rb"):
            pass
    except EnvironmentError:
        raise ValueError("Cannot access certificate file: " + namespace.cert_file)


def validate_options(namespace):
    """Validate any flattened request header option arguments."""
    try:
        start = namespace.start_range
        end = namespace.end_range
    except AttributeError:
        return
    else:
        namespace.ocp_range = None
        del namespace.start_range
        del namespace.end_range
        if start or end:
            start = start if start else 0
            end = end if end else ""
            namespace.ocp_range = "bytes={}-{}".format(start, end)


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
                message = "Directory {} does not exist, and cannot be created: {}"
                raise ValueError(message.format(file_dir, exp))
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

def validate_pool_settings(ns, parser):
    """Custom parsing to enfore that either PaaS or IaaS instances are configured
    in the add pool request body.
    """
    if not ns.json_file:
        groups = ['pool.cloud_service_configuration', 'pool.virtual_machine_configuration']
        parser.parse_mutually_exclusive(ns, True, groups)

        paas_sizes = ['small', 'medium', 'large', 'extralarge']
        if ns.vm_size and ns.vm_size.lower() in paas_sizes and not ns.os_family:
            message = ("The selected VM size in incompatible with Virtual Machine Configuration. "
                       "Please swap for the IaaS equivalent: Standard_A1 (small), Standard_A2 "
                       "(medium), Standard_A3 (large), or Standard_A4 (extra large).")
            raise ValueError(message)
