# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json


def load_node_agent_skus(prefix, **kwargs):  # pylint: disable=unused-argument
    from msrest.exceptions import ClientRequestError
    from azure.batch.models import BatchErrorException
    from azure.cli.command_modules.batch._client_factory import account_client_factory
    from azure.cli.core._config import az_config
    all_images = []
    client_creds = {}
    client_creds['account_name'] = az_config.get('batch', 'account', None)
    client_creds['account_key'] = az_config.get('batch', 'access_key', None)
    client_creds['account_endpoint'] = az_config.get('batch', 'endpoint', None)
    try:
        client = account_client_factory(client_creds)
        skus = client.list_node_agent_skus()
        for sku in skus:
            for image in sku['verifiedImageReferences']:
                all_images.append("{}:{}:{}:{}".format(
                    image['publisher'],
                    image['offer'],
                    image['sku'],
                    image['version']))
        return all_images
    except (ClientRequestError, BatchErrorException):
        return []


# TYPES VALIDATORS

def datetime_format(value):
    """Validate the correct format of a datetime string and deserialize."""
    from msrest.serialization import Deserializer
    from msrest.exceptions import DeserializationError
    try:
        datetime_obj = Deserializer.deserialize_iso(value)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(value))
    return datetime_obj


def duration_format(value):
    """Validate the correct format of a timespan string and deserilize."""
    from msrest.serialization import Deserializer
    from msrest.exceptions import DeserializationError
    try:
        duration_obj = Deserializer.deserialize_duration(value)
    except DeserializationError:
        message = "Argument {} is not in a valid ISO-8601 duration format"
        raise ValueError(message.format(value))
    return duration_obj


def metadata_item_format(value):
    """Space separated values in 'key=value' format."""
    try:
        data_name, data_value = value.split('=')
    except ValueError:
        message = ("Incorrectly formatted metadata. "
                   "Argmuent values should be in the format a=b c=d")
        raise ValueError(message)
    return {'name': data_name, 'value': data_value}


def environment_setting_format(value):
    """Space separated values in 'key=value' format."""
    try:
        env_name, env_value = value.split('=')
    except ValueError:
        message = ("Incorrectly formatted enviroment settings. "
                   "Argmuent values should be in the format a=b c=d")
        raise ValueError(message)
    return {'name': env_name, 'value': env_value}


def application_package_reference_format(value):
    """Space separated application IDs with optional version in 'id[#version]' format."""
    app_reference = value.split('#', 1)
    package = {'application_id': app_reference[0]}
    try:
        package['version'] = app_reference[1]
    except IndexError:  # No specified version - ignore
        pass
    return package


def certificate_reference_format(value):
    """Space separated certificate thumbprints."""
    cert = {'thumbprint': value, 'thumbprint_algorithm': 'sha1'}
    return cert


def task_id_ranges_format(value):
    """Space separated number ranges in 'start-end' format."""
    try:
        start, end = [int(i) for i in value.split('-')]
    except ValueError:
        message = ("Incorrectly formatted task ID range. "
                   "Argmuent values should be numbers in the format 'start-end'")
        raise ValueError(message)
    return {'start': start, 'end': end}


def resource_file_format(value):
    """Space separated resource references in filename=blobsource format."""
    try:
        file_name, blob_source = value.split('=')
    except ValueError:
        message = ("Incorrectly formatted resource reference. "
                   "Argmuent values should be in the format filename=blobsource")
        raise ValueError(message)
    return {'file_path': file_name, 'blob_source': blob_source}


# COMMAND NAMESPACE VALIDATORS

def validate_required_parameter(ns, parser):
    """Validates required parameters in Batch complex objects"""
    if not parser.done:
        parser.parse(ns)


def storage_account_id(namespace):
    """Validate storage account name"""
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    if (namespace.storage_account and not
            ('/providers/Microsoft.ClassicStorage/storageAccounts/' in namespace.storage_account or
             '/providers/Microsoft.Storage/storageAccounts/' in namespace.storage_account)):
        storage_client = get_mgmt_service_client(ResourceType.MGMT_STORAGE)
        acc = storage_client.storage_accounts.get_properties(namespace.resource_group_name,
                                                             namespace.storage_account)
        if not acc:
            raise ValueError("Storage account named '{}' not found in the resource group '{}'.".
                             format(namespace.storage_account, namespace.resource_group_name))
        namespace.storage_account = acc.id  # pylint: disable=no-member


def keyvault_id(namespace):
    """Validate storage account name"""
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    if not namespace.keyvault:
        return
    if '/providers/Microsoft.KeyVault/vaults/' in namespace.keyvault:
        resource = namespace.keyvault.split('/')
        kv_name = resource[resource.index('Microsoft.KeyVault') + 2]
        kv_rg = resource[resource.index('resourceGroups') + 1]
    else:
        kv_name = namespace.keyvault
        kv_rg = namespace.resource_group_name
    try:
        keyvault_client = get_mgmt_service_client(KeyVaultManagementClient)
        vault = keyvault_client.vaults.get(kv_rg, kv_name)
        if not vault:
            raise ValueError("KeyVault named '{}' not found in the resource group '{}'.".
                             format(kv_name, kv_rg))
        namespace.keyvault = vault.id  # pylint: disable=no-member
        namespace.keyvault_url = vault.properties.vault_uri
    except Exception as exp:
        raise ValueError('Invalid KeyVault reference: {}\n{}'.format(namespace.keyvault, exp))


def application_enabled(namespace):
    """Validates account has auto-storage enabled"""
    from azure.mgmt.batch import BatchManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    client = get_mgmt_service_client(BatchManagementClient)
    acc = client.batch_account.get(namespace.resource_group_name, namespace.account_name)
    if not acc:
        raise ValueError("Batch account '{}' not found.".format(namespace.account_name))
    if not acc.auto_storage or not acc.auto_storage.storage_account_id:  # pylint: disable=no-member
        raise ValueError("Batch account '{}' needs auto-storage enabled.".
                         format(namespace.account_name))


def validate_pool_resize_parameters(namespace):
    """Validate pool resize parameters correct"""
    if not namespace.abort and not namespace.target_dedicated_nodes:
        raise ValueError("The target-dedicated-nodes parameter is required to resize the pool.")


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
        with open(namespace.certificate_file, "rb"):
            pass
    except EnvironmentError:
        raise ValueError("Cannot access certificate file: " + namespace.certificate_file)


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

# CUSTOM REQUEST VALIDATORS


def validate_pool_settings(ns, parser):
    """Custom parsing to enfore that either PaaS or IaaS instances are configured
    in the add pool request body.
    """
    if not ns.json_file:
        if ns.node_agent_sku_id and not ns.image:
            raise ValueError("Missing required argument: --image")
        if ns.image:
            ns.version = 'latest'
            try:
                ns.publisher, ns.offer, ns.sku = ns.image.split(':', 2)
            except ValueError:
                message = ("Incorrect format for VM image URN. Should be in the format: \n"
                           "'publisher:offer:sku[:version]'")
                raise ValueError(message)
            try:
                ns.sku, ns.version = ns.sku.split(':', 1)
            except ValueError:
                pass
            del ns.image
        groups = ['pool.cloud_service_configuration', 'pool.virtual_machine_configuration']
        parser.parse_mutually_exclusive(ns, True, groups)

        paas_sizes = ['small', 'medium', 'large', 'extralarge']
        if ns.vm_size and ns.vm_size.lower() in paas_sizes and not ns.os_family:
            message = ("The selected VM size is incompatible with Virtual Machine Configuration. "
                       "Please swap for the equivalent: Standard_A1 (small), Standard_A2 "
                       "(medium), Standard_A3 (large), or Standard_A4 (extra large).")
            raise ValueError(message)
        if ns.auto_scale_formula:
            ns.enable_auto_scale = True


def validate_cert_settings(ns):
    """Custom parsing for certificate commands - adds default thumbprint
    algorithm.
    """
    ns.thumbprint_algorithm = 'sha1'
