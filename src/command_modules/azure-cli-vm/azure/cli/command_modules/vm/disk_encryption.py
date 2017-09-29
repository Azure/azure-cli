# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
from azure.cli.core.commands.arm import parse_resource_id
from azure.cli.core.commands import LongRunningOperation
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError
from .custom import set_vm, _compute_client_factory, get_vmss_instance_view
logger = azlogging.get_az_logger(__name__)

_DATA_VOLUME_TYPE = 'DATA'
_STATUS_ENCRYPTED = 'Encrypted'

vm_extension_info = {
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

vmss_extension_info = {
    'Linux': {
        'publisher': 'Microsoft.Azure.Security',
        'name': vm_extension_info['Linux']['name'],
        'version': '1.1'
    },
    'Windows': {
        'publisher': 'Microsoft.Azure.Security',
        'name': vm_extension_info['Windows']['name'],
        'version': '2.1'
    }
}


def encrypt_vm(resource_group_name, vm_name,  # pylint: disable=too-many-locals, too-many-statements
               aad_client_id,
               disk_encryption_keyvault,
               aad_client_secret=None, aad_client_cert_thumbprint=None,
               key_encryption_keyvault=None,
               key_encryption_key=None,
               key_encryption_algorithm='RSA-OAEP',
               volume_type=None):
    '''
    Enable disk encryption on OS disk, Data disks, or both
    :param str aad_client_id: Client ID of AAD app with permissions to write secrets to KeyVault
    :param str aad_client_secret: Client Secret of AAD app with permissions to
    write secrets to KeyVault
    :param str aad_client_cert_thumbprint: Thumbprint of AAD app certificate with permissions
    to write secrets to KeyVault
    :param str disk_encryption_keyvault:the KeyVault where generated encryption key will be placed
    :param str key_encryption_key: KeyVault key name or URL used to encrypt the disk encryption key
    :param str key_encryption_keyvault: the KeyVault containing the key encryption key
    used to encrypt the disk encryption key. If missing, CLI will use --disk-encryption-keyvault
    '''
    # pylint: disable=no-member
    compute_client = _compute_client_factory()
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = _is_linux_vm(os_type)
    extension = vm_extension_info[os_type]
    backup_encryption_settings = vm.storage_profile.os_disk.encryption_settings
    vm_encrypted = backup_encryption_settings.enabled if backup_encryption_settings else False

    # 1. First validate arguments

    if not aad_client_cert_thumbprint and not aad_client_secret:
        raise CLIError('Please provide either --aad-client-id or --aad-client-cert-thumbprint')

    if volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError('VM has data disks, please supply --volume-type')
        else:
            volume_type = 'OS'

    # encryption is not supported on all linux distros, but service never tells you
    # so let us verify at the client side
    if is_linux:
        image_reference = getattr(vm.storage_profile, 'image_reference', None)
        if image_reference:
            result, message = _check_encrypt_is_supported(image_reference, volume_type)
            if not result:
                logger.warning(message)

    # sequence_version should be unique
    sequence_version = uuid.uuid4()

    # retrieve keyvault details
    disk_encryption_keyvault_url = _get_key_vault_base_url(
        (parse_resource_id(disk_encryption_keyvault))['name'])

    # disk encryption key itself can be further protected, so let us verify
    if key_encryption_key:
        key_encryption_keyvault = key_encryption_keyvault or disk_encryption_keyvault
        if '://' not in key_encryption_key:  # appears a key name
            key_encryption_key = _get_keyvault_key_url(
                (parse_resource_id(key_encryption_keyvault))['name'], key_encryption_key)

    # 2. we are ready to provision/update the disk encryption extensions
    # The following logic was mostly ported from xplat-cli
    public_config = {
        'AADClientID': aad_client_id,
        'AADClientCertThumbprint': aad_client_cert_thumbprint,
        'KeyVaultURL': disk_encryption_keyvault_url,
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption',
        'KeyEncryptionKeyURL': key_encryption_key,
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

    # verify the extension was ok
    extension_result = compute_client.virtual_machine_extensions.get(
        resource_group_name, vm_name, extension['name'], 'instanceView')
    if extension_result.provisioning_state != 'Succeeded':
        raise CLIError('Extension needed for disk encryption was not provisioned correctly')
    if not (extension_result.instance_view.statuses and
            extension_result.instance_view.statuses[0].message):
        raise CLIError('Could not found url pointing to the secret for disk encryption')

    # 3. update VM's storage profile with the secrets
    status_url = extension_result.instance_view.statuses[0].message

    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    secret_ref = KeyVaultSecretReference(secret_url=status_url,
                                         source_vault=SubResource(disk_encryption_keyvault))

    key_encryption_key_obj = None
    if key_encryption_key:
        key_encryption_key_obj = KeyVaultKeyReference(key_encryption_key,
                                                      SubResource(key_encryption_keyvault))

    disk_encryption_settings = DiskEncryptionSettings(disk_encryption_key=secret_ref,
                                                      key_encryption_key=key_encryption_key_obj,
                                                      enabled=True)
    if vm_encrypted:
        # stop the vm before update if the vm is already encrypted
        logger.warning("Deallocating the VM before updating encryption settings...")
        compute_client.virtual_machines.deallocate(resource_group_name, vm_name).result()
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    set_vm(vm)

    if vm_encrypted:
        # and start after the update
        logger.warning("Restarting the VM after the update...")
        compute_client.virtual_machines.start(resource_group_name, vm_name).result()

    if is_linux and volume_type != _DATA_VOLUME_TYPE:
        # TODO: expose a 'wait' command to do the monitor and handle the reboot
        logger.warning("The encryption request was accepted. Please use 'show' command to monitor "
                       "the progress. If you see 'VMRestartPending', please restart the VM, and "
                       "the encryption will finish shortly")


def decrypt_vm(resource_group_name, vm_name, volume_type=None, force=False):
    '''
    Disable disk encryption on OS disk, Data disks, or both
    '''
    compute_client = _compute_client_factory()
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    # pylint: disable=no-member
    os_type = vm.storage_profile.os_disk.os_type.value

    # 1. be nice, figure out the default volume type and also verify VM will not be busted
    is_linux = _is_linux_vm(os_type)
    if is_linux:
        if volume_type:
            if not force:
                if volume_type == _DATA_VOLUME_TYPE:
                    status = show_vm_encryption_status(resource_group_name, vm_name)
                    if status['osDisk'] == _STATUS_ENCRYPTED:
                        raise CLIError("Linux VM's OS disk is encrypted. Disabling encryption on data "
                                       "disk can render the VM unbootable. Use '--force' "
                                       "to ingore the warning")
                else:
                    raise CLIError("Only Data disks can have encryption disabled in a Linux VM. "
                                   "Use '--force' to ingore the warning")
        else:
            volume_type = _DATA_VOLUME_TYPE
    elif volume_type is None:
        if vm.storage_profile.data_disks:
            raise CLIError("VM has data disks, please specify --volume-type")

    # sequence_version should be incremented since encryptions occurred before
    extension = vm_extension_info[os_type]
    sequence_version = uuid.uuid4()

    # 2. update the disk encryption extension
    # The following logic was mostly ported from xplat-cli
    public_config = {
        'VolumeType': volume_type,
        'EncryptionOperation': 'DisableEncryption',
        'SequenceVersion': sequence_version,
    }

    from azure.mgmt.compute.models import VirtualMachineExtension, DiskEncryptionSettings

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

    # 3. Remove the secret from VM's storage profile
    extension_result = compute_client.virtual_machine_extensions.get(resource_group_name, vm_name,
                                                                     extension['name'],
                                                                     'instanceView')
    if extension_result.provisioning_state != 'Succeeded':
        raise CLIError("Extension updating didn't succeed")

    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    disk_encryption_settings = DiskEncryptionSettings(enabled=False)
    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    set_vm(vm)


def show_vm_encryption_status(resource_group_name, vm_name):
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
    # The following logic was mostly ported from xplat-cli
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = _is_linux_vm(os_type)
    encryption_status['osType'] = os_type
    extension = vm_extension_info[os_type]
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
        except Exception:  # pylint: disable=broad-except
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
            if about_data_disk and extension_result.settings.get('EncryptionOperation', None) == 'EnableEncryption':
                encryption_status['dataDisk'] = _STATUS_ENCRYPTED

    return encryption_status


def _is_linux_vm(os_type):
    return os_type.lower() == 'linux'


def _get_keyvault_key_url(keyvault_name, key_name):
    from azure.cli.core._profile import Profile

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile().get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
    client = KeyVaultClient(KeyVaultAuthentication(get_token))
    result = client.get_key(_get_key_vault_base_url(keyvault_name), key_name, '')
    return result.key.kid  # pylint: disable=no-member


def _get_key_vault_base_url(vault_name):
    from azure.cli.core._profile import CLOUD
    suffix = CLOUD.suffixes.keyvault_dns
    return 'https://{}{}'.format(vault_name, suffix)


def _check_encrypt_is_supported(image_reference, volume_type):
    offer = getattr(image_reference, 'offer', None)
    publisher = getattr(image_reference, 'publisher', None)
    sku = getattr(image_reference, 'sku', None)

    # custom image?
    if not offer or not publisher or not sku:
        return (True, None)

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
        if (image['publisher'].lower() == publisher.lower() and
                sku.lower().startswith(image['sku'].lower()) and
                offer.lower().startswith(image['offer'].lower())):
            return (True, None)

    sku_list = ['{} {}'.format(a['offer'], a['sku']) for a in supported]

    message = "Encryption might fail as current VM uses a distro not in the known list, which are '{}'".format(sku_list)
    return (False, message)


def _handles_default_volume_type_for_vmss_encryption(is_linux, volume_type, force):
    if is_linux:
        volume_type = volume_type or 'DATA'
        if volume_type != 'DATA':
            msg = 'OS disk encyrption is not yet supported for Linux VM scale sets'
            if force:
                logger.warning(msg)
            else:
                raise CLIError(msg)
    else:
        volume_type = volume_type or 'ALL'
    return volume_type


def encrypt_vmss(resource_group_name, vmss_name,  # pylint: disable=too-many-locals, too-many-statements
                 disk_encryption_keyvault,
                 key_encryption_keyvault=None,
                 key_encryption_key=None,
                 key_encryption_algorithm='RSA-OAEP',
                 volume_type=None,
                 force=False):
    '''
    :param str disk_encryption_keyvault:the KeyVault where generated encryption key will be placed
    :param str key_encryption_key: KeyVault key name or URL used to encrypt the disk encryption key
    :param str key_encryption_keyvault: the KeyVault containing the key encryption key
    used to encrypt the disk encryption key. If missing, CLI will use --disk-encryption-keyvault
    :param bool force: continue by ignoring client side validation errors
    '''
    from azure.cli.core.profiles import get_sdk, ResourceType
    # pylint: disable=no-member
    UpgradeMode, VirtualMachineScaleSetExtension, VirtualMachineScaleSetExtensionProfile = get_sdk(
        ResourceType.MGMT_COMPUTE, 'UpgradeMode', 'VirtualMachineScaleSetExtension',
        'VirtualMachineScaleSetExtensionProfile', mod='models')

    compute_client = _compute_client_factory()
    vmss = compute_client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    os_type = 'Linux' if vmss.virtual_machine_profile.os_profile.linux_configuration else 'Windows'
    is_linux = _is_linux_vm(os_type)
    extension = vmss_extension_info[os_type]

    # 1. First validate arguments
    volume_type = _handles_default_volume_type_for_vmss_encryption(is_linux, volume_type, force)

    # encryption is not supported on all linux distros, but service never tells you
    # so let us verify at the client side
    if is_linux:
        image_reference = getattr(vmss.virtual_machine_profile.storage_profile, 'image_reference', None)
        if image_reference:
            result, message = _check_encrypt_is_supported(image_reference, volume_type)
            if not result:
                logger.warning(message)

    # retrieve keyvault details
    disk_encryption_keyvault_url = _get_key_vault_base_url((parse_resource_id(disk_encryption_keyvault))['name'])

    # disk encryption key itself can be further protected, so let us verify
    if key_encryption_key:
        key_encryption_keyvault = key_encryption_keyvault or disk_encryption_keyvault
        if '://' not in key_encryption_key:  # appears a key name
            key_encryption_key = _get_keyvault_key_url(
                (parse_resource_id(key_encryption_keyvault))['name'], key_encryption_key)

    #  to avoid bad server errors, ensure the vault has the right configurations
    _verify_keyvault_good_for_encryption(disk_encryption_keyvault, key_encryption_keyvault, vmss, force)

    # 2. we are ready to provision/update the disk encryption extensions
    public_config = {
        'KeyVaultURL': disk_encryption_keyvault_url,
        'KeyEncryptionKeyURL': key_encryption_key or '',
        "KeyVaultResourceId": disk_encryption_keyvault,
        "KekVaultResourceId": key_encryption_keyvault if key_encryption_key else '',
        'KeyEncryptionAlgorithm': key_encryption_algorithm if key_encryption_key else '',
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption'
    }

    ext = VirtualMachineScaleSetExtension(name=extension['name'],
                                          publisher=extension['publisher'],
                                          type=extension['name'],
                                          type_handler_version=extension['version'],
                                          settings=public_config,
                                          auto_upgrade_minor_version=True,
                                          force_update_tag=uuid.uuid4())
    if not vmss.virtual_machine_profile.extension_profile:
        vmss.virtual_machine_profile.extension_profile = VirtualMachineScaleSetExtensionProfile([])
    vmss.virtual_machine_profile.extension_profile.extensions.append(ext)
    poller = compute_client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)
    LongRunningOperation()(poller)
    _show_post_action_message(resource_group_name, vmss.name, vmss.upgrade_policy.mode == UpgradeMode.manual, True)


def decrypt_vmss(resource_group_name, vmss_name, volume_type=None, force=False):
    from azure.cli.core.profiles import get_sdk, ResourceType
    UpgradeMode, VirtualMachineScaleSetExtension = get_sdk(
        ResourceType.MGMT_COMPUTE, 'UpgradeMode', 'VirtualMachineScaleSetExtension', mod='models')
    compute_client = _compute_client_factory()
    vmss = compute_client.virtual_machine_scale_sets.get(resource_group_name, vmss_name)
    os_type = 'Linux' if vmss.virtual_machine_profile.os_profile.linux_configuration else 'Windows'
    is_linux = _is_linux_vm(os_type)
    extension = vmss_extension_info[os_type]

    # 1. be nice, figure out the default volume type
    volume_type = _handles_default_volume_type_for_vmss_encryption(is_linux, volume_type, force)

    # 2. update the disk encryption extension
    public_config = {
        'VolumeType': volume_type,
        'EncryptionOperation': 'DisableEncryption',
    }

    ext = VirtualMachineScaleSetExtension(name=extension['name'],
                                          publisher=extension['publisher'],
                                          type=extension['name'],
                                          type_handler_version=extension['version'],
                                          settings=public_config,
                                          auto_upgrade_minor_version=True,
                                          force_update_tag=uuid.uuid4())
    if (not vmss.virtual_machine_profile.extension_profile or
            not vmss.virtual_machine_profile.extension_profile.extensions):
        extensions = []
    else:
        extensions = vmss.virtual_machine_profile.extension_profile.extensions

    ade_extension = [x for x in extensions if
                     x.type.lower() == extension['name'].lower() and x.publisher.lower() == extension['publisher'].lower()]  # pylint: disable=line-too-long
    if not ade_extension:
        raise CLIError("VM scale set '{}' was not encrypted".format(vmss_name))

    index = vmss.virtual_machine_profile.extension_profile.extensions.index(ade_extension[0])
    vmss.virtual_machine_profile.extension_profile.extensions[index] = ext
    poller = compute_client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss_name, vmss)
    LongRunningOperation()(poller)
    _show_post_action_message(resource_group_name, vmss.name, vmss.upgrade_policy.mode == UpgradeMode.manual, False)


def _show_post_action_message(resource_group_name, vmss_name, maunal_mode, enable):
    msg = ''
    if maunal_mode:
        msg = ("With manual upgrade mode, you will need to run 'az vmss update-instances -g {} -n {} "
               "--instance-ids \"*\"' to propagate the change.\n".format(resource_group_name, vmss_name))
    msg += ("Note, {} encryption will take a while to finish. Please query the status using "
            "'az vmss encryption show -g {} -n {}'. For Linux VM, you will lose the access during the period".format(
                'enabling' if enable else 'disabling', resource_group_name, vmss_name))
    logger.warning(msg)


def show_vmss_encryption_status(resource_group_name, vmss_name):
    encryption_ext_names = [v['name'] for v in vmss_extension_info.values()]
    views = get_vmss_instance_view(resource_group_name, vmss_name)
    if not views.extensions or not [e for e in views.extensions if e.name in encryption_ext_names]:
        raise CLIError("'{}' is not encrypted yet".format(vmss_name))

    views = get_vmss_instance_view(resource_group_name, vmss_name, instance_id='*')
    result = [{'disks': v.disks, 'extensions': v.extensions} for v in views]
    # get rid of unrelaed disk status
    for r in result:
        for d in r['disks']:
            d.statuses = [s for s in d.statuses if s.code.startswith('EncryptionState')]
        r['encryption-extension'] = next((e for e in (r['extensions'] or []) if e.name in encryption_ext_names), None)
        r.pop('extensions')  # we don't need this array any more
    return result


def _verify_keyvault_good_for_encryption(disk_vault_id, kek_vault_id, vmss, force):
    def _report_client_side_validation_error(msg):
        if force:
            logger.warning(msg)
        else:
            raise CLIError(msg)

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.keyvault import KeyVaultManagementClient
    client = get_mgmt_service_client(KeyVaultManagementClient).vaults
    disk_vault_resource_info = parse_resource_id(disk_vault_id)
    key_vault = client.get(disk_vault_resource_info['resource_group'], disk_vault_resource_info['name'])

    # ensure vault has 'EnabledForDiskEncryption' permission
    if not key_vault.properties.enabled_for_disk_encryption:
        _report_client_side_validation_error("keyvault '{}' is not enabled for disk encryption. ".format(
            disk_vault_resource_info['resource_name']))

    if kek_vault_id:
        kek_vault_info = parse_resource_id(kek_vault_id)
        if disk_vault_resource_info['name'].lower() != kek_vault_info['name'].lower():
            client.get(kek_vault_info['resource_group'], kek_vault_info['name'])

    # verify subscription mataches
    vmss_resource_info = parse_resource_id(vmss.id)
    if vmss_resource_info['subscription'].lower() != disk_vault_resource_info['subscription'].lower():
        _report_client_side_validation_error(
            "VM scale set's subscription doesn't match keyvault's subscription. Encryption might fail")

    # verify region matches
    if key_vault.location.replace(' ', '').lower() != vmss.location.replace(' ', '').lower():
        _report_client_side_validation_error(
            "VM scale set's region doesn't match keyvault's region. Encryption might fail")
