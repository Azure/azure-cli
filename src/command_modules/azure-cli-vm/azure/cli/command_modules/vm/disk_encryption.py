from msrestazure.azure_exceptions import CloudError
import azure.cli.core.azlogging as azlogging
from azure.cli.core._util import CLIError
from .custom import get_vm, set_vm, _compute_client_factory
logger = azlogging.get_az_logger(__name__)

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


def keyvault_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.keyvault import KeyVaultManagementClient
    return get_mgmt_service_client(KeyVaultManagementClient)


# TODO: add client cert support, key encryption key, etc
def encrypt_disk(resource_group_name, vm_name,
                 aad_client_id, aad_client_secret,
                 keyvault, key_encryption_key_url=None, key_encryption_vault_id=None,
                 client_cert_thumbprint=None, key_encryption_algorithm='RSA-OAEP',
                 volume_type=None):
    # pylint: disable=no-member
    vm = get_vm(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = os_type.lower() == 'linux'
    extension = extension_info[os_type]
    if volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError('VM has data disks, please supply --volume-type')
        else:
            volume_type = 'OS'

    if is_linux:
        image_reference = getattr(vm.storage_profile, 'image_reference', None)
        if image_reference:
            _check_encrypt_is_supported(image_reference, volume_type)

    # TODO: support passphase for linux
    # TODO: cross check the secret stuff
    compute_client = _compute_client_factory()
    sequence_version = _get_sequence_version(compute_client, resource_group_name,
                                             vm_name, extension['name'])

    from azure.cli.core.commands.arm import parse_resource_id, is_valid_resource_id
    keyvault_client = keyvault_client_factory()
    if is_valid_resource_id(keyvault):
        res = parse_resource_id(keyvault)
        keyvault_info = keyvault_client.vaults.get(res['resource_group'], res['name'])
    else:
        result = keyvault_client.vaults.list()
        temp = next((k for k in result if k.name == keyvault), None)
        if not temp:
            raise CloudError("'{}' is not found under subscription".format(keyvault))
        res = parse_resource_id(temp.id)  # 'list' doesn't return all the info, so need a 'get'
        keyvault_info = keyvault_client.vaults.get(res['resource_group'], res['name'])

    keyvault_url = keyvault_info.properties.vault_uri

    public_config = {
        'AADClientID': aad_client_id,
        'AADClientCertThumbprint': client_cert_thumbprint,
        'KeyVaultURL': keyvault_url,
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption',
        'KeyEncryptionKeyURL': key_encryption_key_url,
        'KeyEncryptionAlgorithm': key_encryption_algorithm,  # TODO cross check
        'SequenceVersion': sequence_version,
    }
    private_config = {
        'AADClientSecret': aad_client_secret if is_linux else (aad_client_secret or '')
    }

    # If keyEncryptionKeyUrl is not null but keyEncryptionAlgorithm is,
    # use the default key encryption algorithm
    # if(!utils.stringIsNullOrEmpty(options.keyEncryptionKeyUrl)) {
    #    if(utils.stringIsNullOrEmpty(options.keyEncryptionAlgorithm)) {
    #      params.keyEncryptionAlgorithm = vmConstants.EXTENSIONS.DEFAULT_KEY_ENCRYPTION_ALGORITHM
    #    }
    # }

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

    vm = get_vm(resource_group_name, vm_name)
    secret_ref = KeyVaultSecretReference(secret_url=status_url,
                                         source_vault=SubResource(keyvault_info.id))
    disk_encryption_settings = DiskEncryptionSettings(disk_encryption_key=secret_ref,
                                                      key_encryption_key=None,  # TODO key_encryption_key_url,
                                                      enabled=True)
    # Cross check the xplat's stuff

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)


def disable_disk_encryption(resource_group_name, vm_name, volume_type=None):
    vm = get_vm(resource_group_name, vm_name)
    # pylint: disable=no-member
    os_type = vm.storage_profile.os_disk.os_type.value

    # be nice, figure out the default volume type
    is_linux = os_type.lower() == 'linux'
    if is_linux:
        if volume_type and volume_type != 'DATA':
            raise CLIError("Only data disk is supported to disable on Linux VM")
        else:
            volume_type = 'DATA'
    elif volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError("VM has data disks, please specify --volume-type")

    extension = extension_info[os_type]
    compute_client = _compute_client_factory()
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

    vm = get_vm(resource_group_name, vm_name)
    disk_encryption_settings = DiskEncryptionSettings(enabled=False)

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)


def show_encryption_status(resource_group_name, vm_name):
    encryption_status = {
        'osVolumeEncrypted': 'NotEncrypted',
        'osVolumeEncryptionSettings': None,
        'dataVolumesEncrypted': 'NotEncrypted'
    }
    vm = get_vm(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = os_type.lower() == 'linux'
    extension = extension_info[os_type]
    compute_client = _compute_client_factory()
    extension_result = compute_client.virtual_machine_extensions.get(resource_group_name, vm_name,
                                                                     extension['name'], 'instanceView')
    logger.debug(extension_result)
    encryption_status = {}
    if extension_result.instance_view.statuses:
        encryption_status['progressMessage'] = extension_result.instance_view.statuses[0].message

    substatus_message = None
    if getattr(extension_result.instance_view, 'substatuses', None):
        substatus_message = extension_result.instance_view.substatuses[0].message


    encryption_status['osVolumeEncryptionSettings'] = vm.storage_profile.os_disk.encryption_settings

    import json
    if is_linux:
        try: 
            message_object = json.loads(substatus_message)
        except:
            message_object = None # outdated versions of guest agent produce messages that cannot be parsed

        if message_object and ('os' in message_object):
            encryption_status['osVolumeEncrypted'] = message_object['os']
        else:
            encryption_status['osVolumeEncrypted'] = 'Unknown'

        if message_object and 'data' in message_object:
            encryption_status['dataVolumesEncrypted'] = message_object['data']
        else:
            encryption_status['dataVolumesEncrypted'] = 'Unknown'
    else:
        # Windows - get os and data volume encryption state from the vm model 
        if encryption_status['osVolumeEncryptionSettings'].enabled and encryption_status['osVolumeEncryptionSettings'].disk_encryption_key.secret_url:
            encryption_status['osVolumeEncrypted'] = 'Encrypted'

        if extension_result.provisioning_state == 'Succeeded':
            volume_type = extension_result.settings.get('VolumeType', None)
            if not volume_type or volume_type.lower() != 'os':
                encryption_status['dataVolumesEncrypted'] = 'Encrypted'

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


def _check_encrypt_is_supported(image_reference, volume_type):
    offer = getattr(image_reference, 'offer', None)
    publisher = getattr(image_reference, 'publisher', None)
    sku = getattr(image_reference, 'sku', None)
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

    if volume_type.lower() == 'data':
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
    message = "Encryption is not suppored for current VM. Supported Linux skus are '{}'".format(sku_list)
    raise CLIError(message)
