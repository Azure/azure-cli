# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.azure_exceptions import CloudError
from azure.cli.core.commands.arm import parse_resource_id, is_valid_resource_id
import azure.cli.core.azlogging as azlogging
from azure.cli.core._util import CLIError
from .custom import set_vm, _compute_client_factory
logger = azlogging.get_az_logger(__name__)

_DATA_VOLUME_TYPE = 'DATA'
_STATUS_ENCRYPTED = 'Encrypted'

extension_info = {
    'Linux': {
        'publisher': 'Microsoft.Azure.Security',
        'name': 'AzureDiskEncryptionForLinux',
        'version': '0.1'
    },
    'Windows': {
        'publisher': 'Microsoft.Azure.Security',
        'name': 'AzureDiskEncryption',
        'version': '1.1'
    }
}


def keyvault_mgmt_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.keyvault import KeyVaultManagementClient
    return get_mgmt_service_client(KeyVaultManagementClient)


def enable(resource_group_name, vm_name,  # pylint: disable=too-many-arguments,too-many-locals, too-many-statements
           aad_client_id,
           disk_encryption_keyvault,
           aad_client_secret=None, aad_client_cert_thumbprint=None,
           key_encryption_keyvault_id=None,
           key_encryption_key_url=None,
           key_encryption_algorithm='RSA-OAEP',
           volume_type=None):
    '''
    Enable disk encryption on OS disk, Data disks, or both
    :param str aad_client_id: Client ID of AAD app with permissions to write secrets to KeyVault
    :param str aad_client_secret: Client Secret of AAD app with permissions to
    write secrets to KeyVault
    :param str aad_client_cert_thumbprint: Thumbprint of AAD app certificate with permissions
    to write secrets to KeyVaul
    :param str disk_encryption_keyvault:KeyVault where generated encryption key will be placed to
    :param str key_encryption_key_url:Versioned KeyVault URL of the KeyEncryptionKey used to
    encrypt the disk encryption key
    :param str key_encryption_keyvault_id: id of the KeyVault containing the key encryption key
    used to encrypt the disk encryption key. If missing, CLI will derive the value from
    --key-encryption-key-url
    '''
    # pylint: disable=no-member
    compute_client = _compute_client_factory()
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = _is_linux_vm(os_type)
    extension = extension_info[os_type]

    if not aad_client_cert_thumbprint and not aad_client_secret:
        raise CLIError('Please provide either --aad-client-id or --aad-client-cert-thumbprint')

    if volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError('VM has data disks, please supply --volume-type')
        else:
            volume_type = 'OS'

    if is_linux:
        image_reference = getattr(vm.storage_profile, 'image_reference', None)
        if image_reference:
            _check_encrypt_is_supported(image_reference, volume_type)

    # TODO: support passphase for linux if there is ask
    sequence_version = _get_sequence_version(compute_client, resource_group_name,
                                             vm_name, extension['name'])

    keyvault_client = keyvault_mgmt_client_factory()
    if is_valid_resource_id(disk_encryption_keyvault):
        res = parse_resource_id(disk_encryption_keyvault)
        keyvault_info = keyvault_client.vaults.get(res['resource_group'], res['name'])
    else:
        keyvault_info = _look_for_keyvault(keyvault_client, disk_encryption_keyvault,
                                           get_detail=True)
    keyvault_url = keyvault_info.properties.vault_uri

    if key_encryption_key_url and not key_encryption_keyvault_id:
        try:
            from urllib.parse import urlparse
        except ImportError:
            from urlparse import urlparse  # pylint: disable=import-error
        hostname = urlparse(key_encryption_key_url).hostname
        if not hostname:
            raise CLIError('Please provide a full url to --key-encryption-key-url')
        key_encryption_keyvault_id = _look_for_keyvault(keyvault_client,
                                                        hostname.split('.')[0], get_detail=False).id

    public_config = {
        'AADClientID': aad_client_id,
        'AADClientCertThumbprint': aad_client_cert_thumbprint,
        'KeyVaultURL': keyvault_url,
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption',
        'KeyEncryptionKeyURL': key_encryption_key_url,
        'KeyEncryptionAlgorithm': key_encryption_algorithm,
        'SequenceVersion': sequence_version,
    }
    private_config = {
        'AADClientSecret': aad_client_secret if is_linux else (aad_client_secret or '')
    }

    from azure.mgmt.compute.models import (VirtualMachineExtension, DiskEncryptionSettings,
                                           KeyVaultSecretReference, KeyVaultKeyReference,
                                           SubResource)

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
                                  publisher=extension['publisher'],
                                  virtual_machine_extension_type=extension['name'],
                                  protected_settings=private_config,
                                  type_handler_version=extension['version'],
                                  settings=public_config,
                                  auto_upgrade_minor_version=True)

    poller = compute_client.virtual_machine_extensions.create_or_update(
        resource_group_name, vm_name, extension['name'], ext)
    poller.result()

    extension_result = compute_client.virtual_machine_extensions.get(
        resource_group_name, vm_name, extension['name'], 'instanceView')
    if extension_result.provisioning_state != 'Succeeded':
        raise CLIError('Extension needed for disk encryption was not provisioned correctly')
    if not (extension_result.instance_view.statuses and
            extension_result.instance_view.statuses[0].message):
        raise CLIError('Could not found url pointing to the secret from disk encryption')

    status_url = extension_result.instance_view.statuses[0].message

    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    secret_ref = KeyVaultSecretReference(secret_url=status_url,
                                         source_vault=SubResource(keyvault_info.id))

    key_encryption_key_obj = None
    if key_encryption_key_url:
        key_encryption_key_obj = KeyVaultKeyReference(key_encryption_key_url,
                                                      SubResource(key_encryption_keyvault_id))

    disk_encryption_settings = DiskEncryptionSettings(disk_encryption_key=secret_ref,
                                                      key_encryption_key=key_encryption_key_obj,
                                                      enabled=True)

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)


def disable(resource_group_name, vm_name, volume_type=None, force=False):
    '''
    Disable disk encryption on OS disk, Data disks, or both
    '''
    compute_client = _compute_client_factory()
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    # pylint: disable=no-member
    os_type = vm.storage_profile.os_disk.os_type.value

    # be nice, figure out the default volume type
    is_linux = _is_linux_vm(os_type)
    if is_linux:
        if volume_type:
            if volume_type != _DATA_VOLUME_TYPE:
                raise CLIError("Only data disk is supported to disable on Linux VM")
            elif not force:
                status = show_encryption_status(resource_group_name, vm_name)
                if status['osDisk'] == _STATUS_ENCRYPTED:
                    raise CLIError("VM's OS disk is encrypted. Disabling encryption on data "
                                   "disk can still cause VM unbootable. Use '--force' to continue")
        else:
            volume_type = _DATA_VOLUME_TYPE
    elif volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError("VM has data disks, please specify --volume-type")

    extension = extension_info[os_type]
    sequence_version = _get_sequence_version(compute_client, resource_group_name,
                                             vm_name, extension['name'])

    public_config = {
        'VolumeType': volume_type,
        'EncryptionOperation': 'DisableEncryption',
        'SequenceVersion': sequence_version,
    }

    from azure.mgmt.compute.models import (VirtualMachineExtension, DiskEncryptionSettings,
                                           KeyVaultSecretReference, KeyVaultKeyReference,
                                           SubResource)

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
                                  publisher=extension['publisher'],
                                  virtual_machine_extension_type=extension['name'],
                                  type_handler_version=extension['version'],
                                  settings=public_config,
                                  auto_upgrade_minor_version=True)

    poller = compute_client.virtual_machine_extensions.create_or_update(resource_group_name,
                                                                        vm_name,
                                                                        extension['name'], ext)
    poller.result()

    extension_result = compute_client.virtual_machine_extensions.get(resource_group_name, vm_name,
                                                                     extension['name'],
                                                                     'instanceView')
    if extension_result.provisioning_state != 'Succeeded':
        raise CLIError("Extension updating didn't succeed")

    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    disk_encryption_settings = DiskEncryptionSettings(enabled=False)
    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)


def show(resource_group_name, vm_name):
    '''show the encryption status'''
    encryption_status = {
        'osDisk': 'NotEncrypted',
        'osDiskEncryptionSettings': None,
        'dataDisk': 'NotEncrypted',
        'osType': None
    }
    compute_client = _compute_client_factory()
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    # pylint: disable=no-member
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = _is_linux_vm(os_type)
    encryption_status['osType'] = os_type
    extension = extension_info[os_type]
    extension_result = compute_client.virtual_machine_extensions.get(resource_group_name,
                                                                     vm_name,
                                                                     extension['name'],
                                                                     'instanceView')
    logger.debug(extension_result)
    if extension_result.instance_view.statuses:
        encryption_status['progressMessage'] = extension_result.instance_view.statuses[0].message

    substatus_message = None
    if getattr(extension_result.instance_view, 'substatuses', None):
        substatus_message = extension_result.instance_view.substatuses[0].message

    encryption_status['osDiskEncryptionSettings'] = vm.storage_profile.os_disk.encryption_settings

    import json
    if is_linux:
        try:
            message_object = json.loads(substatus_message)
        except json.decoder.JSONDecodeError:
            message_object = None  # might be from outdated extension

        if message_object and ('os' in message_object):
            encryption_status['osDisk'] = message_object['os']
        else:
            encryption_status['osDisk'] = 'Unknown'

        if message_object and 'data' in message_object:
            encryption_status['dataDisk'] = message_object['data']
        else:
            encryption_status['dataDisk'] = 'Unknown'
    else:
        # Windows - get os and data volume encryption state from the vm model
        if (encryption_status['osDiskEncryptionSettings'].enabled and
                encryption_status['osDiskEncryptionSettings'].disk_encryption_key.secret_url):
            encryption_status['osDisk'] = _STATUS_ENCRYPTED

        if extension_result.provisioning_state == 'Succeeded':
            volume_type = extension_result.settings.get('VolumeType', None)
            about_data_disk = not volume_type or volume_type.lower() != 'os'
            if about_data_disk and extension_result.settings.get('EncryptionOperation', None) == 'EnableEncryption':  # pylint: disable=line-too-long
                encryption_status['dataDisk'] = _STATUS_ENCRYPTED

    return encryption_status


def _get_sequence_version(compute_client, resource_group_name, vm_name, extension_name):
    sequence_version = None
    try:
        ext = compute_client.virtual_machine_extensions.get(resource_group_name, vm_name,
                                                            extension_name)
        sequence_version = ext.settings.get('SequenceVersion', None)
        if sequence_version is not None:
            sequence_version += 1
    except CloudError:
        pass
    return sequence_version


def _is_linux_vm(os_type):
    return os_type.lower() == 'linux'


def _look_for_keyvault(keyvault_client, keyvault_name, get_detail):
    result = keyvault_client.vaults.list()
    temp = next((k for k in result if k.name == keyvault_name), None)
    if not temp:
        raise CloudError("'{}' is not found under subscription".format(keyvault_name))
    if get_detail:
        res = parse_resource_id(temp.id)  # 'list' doesn't return all the info, so need a 'get'
        keyvault_info = keyvault_client.vaults.get(res['resource_group'], res['name'])
        return keyvault_info
    else:
        return temp


def _check_encrypt_is_supported(image_reference, volume_type):
    offer = getattr(image_reference, 'offer', None)
    publisher = getattr(image_reference, 'publisher', None)
    sku = getattr(image_reference, 'sku', None)

    # custom image?
    if not offer or not publisher or not sku:
        return True

    supported = [
        {
            'offer': 'RHEL',
            'publisher': 'RedHat',
            'sku': '7.2'
        },
        {
            'offer': 'RHEL',
            'publisher': 'RedHat',
            'sku': '7.3'
        },
        {
            'offer': 'CentOS',
            'publisher': 'OpenLogic',
            'sku': '7.2n'
        },
        {
            'offer': 'Ubuntu',
            'publisher': 'Canonical',
            'sku': '14.04'
        },
        {
            'offer': 'Ubuntu',
            'publisher': 'Canonical',
            'sku': '16.04'
        }]

    if volume_type.upper() == _DATA_VOLUME_TYPE:
        supported.append({
            'offer': 'CentOS',
            'publisher': 'OpenLogic',
            'sku': '7.2'
        },)

    for image in supported:
        if (image['publisher'] == publisher and
                image['sku'] == sku and
                image['offer'].lower().startswith(offer.lower())):
            return True

    sku_list = ['{} {}'.format(a['offer'], a['sku']) for a in supported]
    message = "Encryption is not suppored for current VM. Supported are '{}'".format(sku_list)
    raise CLIError(message)
