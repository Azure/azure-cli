# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
import uuid
import os

from knack.log import get_logger

from azure.cli.core.commands import LongRunningOperation

from azure.cli.command_modules.vm.custom import _is_linux_os_aaz
from azure.cli.command_modules.vm._vm_utils import get_key_vault_base_url, create_data_plane_keyvault_key_client

_DATA_VOLUME_TYPE = 'DATA'
_ALL_VOLUME_TYPE = 'ALL'
_STATUS_ENCRYPTED = 'Encrypted'

logger = get_logger(__name__)

vm_extension_info = {
    'Linux': {
        'publisher': os.environ.get('ADE_TEST_EXTENSION_PUBLISHER') or 'Microsoft.Azure.Security',
        'name': os.environ.get('ADE_TEST_EXTENSION_NAME') or 'AzureDiskEncryptionForLinux',
        'version': '1.1',
        'legacy_version': '0.1'
    },
    'Windows': {
        'publisher': os.environ.get('ADE_TEST_EXTENSION_PUBLISHER') or 'Microsoft.Azure.Security',
        'name': os.environ.get('ADE_TEST_EXTENSION_NAME') or 'AzureDiskEncryption',
        'version': '2.2',
        'legacy_version': '1.1'
    }
}


def _find_existing_ade(vm, use_instance_view=False, ade_ext_info=None):
    if not ade_ext_info:
        ade_ext_info = vm_extension_info['Linux'] if _is_linux_os_aaz(vm) else vm_extension_info['Windows']
    if use_instance_view:
        exts = vm['instanceView'].get('extensions', [])
        r = next((e for e in exts if e['type'].lower().startswith(ade_ext_info['publisher'].lower()) and
                  e['name'].lower() == ade_ext_info['name'].lower()), None)
    else:
        exts = vm.get('resources', [])
        r = next((e for e in exts if (e['publisher'].lower() == ade_ext_info['publisher'].lower() and
                                      e['typePropertiesType'].lower() == ade_ext_info['name'].lower())), None)
    return r


def _detect_ade_status(vm):
    if vm.get('storageProfile', {}).get('osDisk', {}).get('encryptionSettings', []):
        return False, True
    ade_ext_info = vm_extension_info['Linux'] if _is_linux_os_aaz(vm) else vm_extension_info['Windows']
    ade = _find_existing_ade(vm, ade_ext_info=ade_ext_info)
    if ade is None:
        return False, False
    if ade['typeHandlerVersion'].split('.')[0] == ade_ext_info['legacy_version'].split('.', maxsplit=1)[0]:
        return False, True

    return True, False   # we believe impossible to have both old & new ADE


def updateVmEncryptionSetting(cmd, vm, resource_group_name, vm_name, encryption_identity):
    from azure.cli.core.azclierror import ArgumentUsageError
    if encryption_identity.lower() not in (k.lower() for k in vm.get('identity', {}).get('userAssignedIdentities', {}).keys()):
        raise ArgumentUsageError("Encryption Identity should be an ARM Resource ID of one of the "
                                 "user assigned identities associated to the resource")

    updateVm = False

    if not (_encrypt_userid := vm.get('securityProfile', {}).get('encryptionIdentity', {}).get('userAssignedIdentityResourceId', None)) \
       or _encrypt_userid.lower() != encryption_identity.lower():
        updateVm = True

    if updateVm:
        from .aaz.latest.vm import Patch as VMPatchUpdate
        security_profile = {
            'encryption_identity': {
                'user_assigned_identity_resource_id': encryption_identity
            }
        }
        updateEncryptionIdentity = VMPatchUpdate(cli_ctx=cmd.cli_ctx)(command_args={
            'location': vm['location'],
            'vm_name': vm_name,
            'resource_group': resource_group_name,
            'security_profile': security_profile
        })
        result = LongRunningOperation(cmd.cli_ctx)(updateEncryptionIdentity)
        return result is not None and result['provisioningState'] == 'Succeeded'
    logger.info("No changes in identity")
    return True


def updateVmssEncryptionSetting(cmd, vmss, resource_group_name, vmss_name, encryption_identity):
    from azure.cli.core.azclierror import ArgumentUsageError
    if encryption_identity.lower() not in (k.lower() for k in vmss.get('identity', {}).get('userAssignedIdentities', {}).keys()):
        raise ArgumentUsageError("Encryption Identity should be an ARM Resource ID of one of the "
                                 "user assigned identities associated to the resource")

    updateVmss = False
    if vmss['properties']['virtualMachineProfile'].get('securityProfile', {}).get('encryptionIdentity', {}).\
            get('userAssignedIdentityResourceId', '').lower() != encryption_identity.lower():
        updateVmss = True

    if updateVmss:
        from .aaz.latest.vmss import Patch
        virtual_machine_profile = {
            'securityProfile': {
                'encryptionIdentity': {
                    'userAssignedIdentityResourceId': encryption_identity
                }
            }
        }
        updateEncryptionIdentity = Patch(cli_ctx=cmd.cli_ctx)(command_args={
            'vm_scale_set_name': vmss_name,
            'resource_group': resource_group_name,
            'virtual_machine_profile': virtual_machine_profile
        })
        LongRunningOperation(cmd.cli_ctx)(updateEncryptionIdentity)
        result = updateEncryptionIdentity.result()
        return result is not None and result.provisioning_state == 'Succeeded'
    logger.info("No changes in identity")
    return True


def isVersionSuppprtedForEncryptionIdentity(cmd):
    from azure.cli.core.profiles import ResourceType
    from knack.util import CLIError
    if not cmd.supported_api_version(min_api='2023-09-01', resource_type=ResourceType.MGMT_COMPUTE):
        raise CLIError("Usage error: Encryption Identity required API version 2023-09-01 or higher."
                       "You can set the cloud's profile to use the required API Version with:"
                       "az cloud set --profile latest --name <cloud name>")
    return True


def encrypt_vm(cmd, resource_group_name, vm_name,  # pylint: disable=too-many-locals, too-many-statements
               disk_encryption_keyvault,
               aad_client_id=None,
               aad_client_secret=None, aad_client_cert_thumbprint=None,
               key_encryption_keyvault=None,
               key_encryption_key=None,
               key_encryption_algorithm='RSA-OAEP',
               volume_type=None,
               encrypt_format_all=False,
               force=False, encryption_identity=None):
    from azure.mgmt.core.tools import parse_resource_id
    from knack.util import CLIError

    from .operations.vm import VMShow
    vm = VMShow(cli_ctx=cmd.cli_ctx)(command_args={
        'vm_name': vm_name,
        'resource_group': resource_group_name
    })
    is_linux = _is_linux_os_aaz(vm)
    vm_encrypted = bool(vm['storageProfile']['osDisk'].get('encryptionSettings', {}).get('enabled', False))
    _, has_old_ade = _detect_ade_status(vm)

    use_new_ade = not aad_client_id and not has_old_ade
    extension = vm_extension_info['Linux' if is_linux else 'Windows']

    if not use_new_ade and not aad_client_id:
        raise CLIError('Please provide --aad-client-id')

    # 1. First validate arguments
    if not use_new_ade and not aad_client_cert_thumbprint and not aad_client_secret:
        raise CLIError('Please provide either --aad-client-cert-thumbprint or --aad-client-secret')

    if volume_type is None:
        if not is_linux:
            volume_type = _ALL_VOLUME_TYPE
        elif vm['storageProfile'].get('dataDisks', []):
            raise CLIError('VM has data disks, please supply --volume-type')
        else:
            volume_type = 'OS'

    # sequence_version should be unique
    sequence_version = uuid.uuid4()

    # retrieve keyvault details
    disk_encryption_keyvault_url = get_key_vault_base_url(
        cmd.cli_ctx, (parse_resource_id(disk_encryption_keyvault))['name'])

    # disk encryption key itself can be further protected, so let us verify
    if key_encryption_key:
        key_encryption_keyvault = key_encryption_keyvault or disk_encryption_keyvault
    if encryption_identity and isVersionSuppprtedForEncryptionIdentity(cmd):
        result = updateVmEncryptionSetting(cmd, vm, resource_group_name, vm_name, encryption_identity)
        if result:
            logger.info("Encryption Identity successfully set in virtual machine")
        else:
            raise CLIError("Failed to update encryption Identity to the VM")

    #  to avoid bad server errors, ensure the vault has the right configurations
    _verify_keyvault_good_for_encryption(cmd.cli_ctx, disk_encryption_keyvault, key_encryption_keyvault, vm, force)

    # if key name and not key url, get url.
    if key_encryption_key and '://' not in key_encryption_key:  # if key name and not key url
        key_encryption_key = _get_keyvault_key_url(
            cmd.cli_ctx, (parse_resource_id(key_encryption_keyvault))['name'], key_encryption_key)

    # 2. we are ready to provision/update the disk encryption extensions
    # The following logic was mostly ported from xplat-cli
    public_config = {
        'KeyVaultURL': disk_encryption_keyvault_url,
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption' if not encrypt_format_all else 'EnableEncryptionFormatAll',
        'KeyEncryptionKeyURL': key_encryption_key,
        'KeyEncryptionAlgorithm': key_encryption_algorithm,
        'SequenceVersion': str(sequence_version),
    }
    if use_new_ade:
        public_config.update({
            "KeyVaultResourceId": disk_encryption_keyvault,
            "KekVaultResourceId": key_encryption_keyvault if key_encryption_key else '',
        })
    else:
        public_config.update({
            'AADClientID': aad_client_id,
            'AADClientCertThumbprint': aad_client_cert_thumbprint,
        })

    ade_legacy_private_config = {
        'AADClientSecret': aad_client_secret if is_linux else (aad_client_secret or '')
    }

    from .operations.vm_extension import VMExtensionCreate
    poller = VMExtensionCreate(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'vm_name': vm_name,
        'vm_extension_name': extension['name'],
        'location': vm['location'],
        'publisher': extension['publisher'],
        'type': extension['name'],
        'protected_settings': None if use_new_ade else ade_legacy_private_config,
        'type_handler_version': extension['version'] if use_new_ade else extension['legacy_version'],
        'settings': public_config,
        'auto_upgrade_minor_version': True,
    })
    extension_result = LongRunningOperation(cmd.cli_ctx)(poller)

    # verify the extension was ok
    if extension_result['provisioningState'] != 'Succeeded':
        raise CLIError('Extension needed for disk encryption was not provisioned correctly')

    if not use_new_ade:
        if not extension_result.get('instanceView', {}).get('statuses', [{}])[0].get('message', ''):
            raise CLIError('Could not find url pointing to the secret for disk encryption')

        # 3. update VM's storage profile with the secrets
        status_url = extension_result['instanceView']['statuses'][0]['message']

        vm = VMShow(cli_ctx=cmd.cli_ctx)(command_args={
            'vm_name': vm_name,
            'resource_group': resource_group_name
        })

        settings = {
            "storageProfile.osDisk.encryptionSettings.diskEncryptionKey.secretUrl": status_url,
            "storageProfile.osDisk.encryptionSettings.diskEncryptionKey.sourceVault.id": disk_encryption_keyvault,
            "storageProfile.osDisk.encryptionSettings.enabled": "True"
        }
        if key_encryption_key:
            settings.update({
                "storageProfile.osDisk.encryptionSettings.keyEncryptionKey.keyUrl": key_encryption_key,
                "storageProfile.osDisk.encryptionSettings.keyEncryptionKey.sourceVault.id": key_encryption_keyvault
            })
        disk_encryption_settings = " ".join([f"{k}={v}" for k, v in settings.items()])

        if vm_encrypted:
            # stop the vm before update if the vm is already encrypted
            logger.warning("Deallocating the VM before updating encryption settings...")
            from .aaz.latest.vm import Deallocate as VMDeallocate
            VMDeallocate(cli_ctx=cmd.cli_ctx)(command_args={
                'vm_name': vm_name,
                'resource_group': resource_group_name
            })

        from .operations.vm import VMUpdate
        LongRunningOperation(cmd.cli_ctx)(
            VMUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                'set': disk_encryption_settings
            })
        )

        if vm_encrypted:
            # and start after the update
            logger.warning("Restarting the VM after the update...")
            from .aaz.latest.vm import Start as VMStart
            VMStart(cli_ctx=cmd.cli_ctx)(command_args={
                'vm_name': vm_name,
                'resource_group': resource_group_name
            })

    if is_linux and volume_type != _DATA_VOLUME_TYPE:
        old_ade_msg = "If you see 'VMRestartPending', please restart the VM, and the encryption will finish shortly"
        logger.warning("The encryption request was accepted. Please use 'show' command to monitor "
                       "the progress. %s", "" if use_new_ade else old_ade_msg)


def decrypt_vm(cmd, resource_group_name, vm_name, volume_type=None, force=False):
    from knack.util import CLIError

    from .operations.vm import VMShow
    vm = VMShow(cli_ctx=cmd.cli_ctx)(command_args={
        'vm_name': vm_name,
        'resource_group': resource_group_name,
    })
    has_new_ade, has_old_ade = _detect_ade_status(vm)
    if not has_new_ade and not has_old_ade:
        logger.warning('Azure Disk Encryption is not enabled')
        return
    is_linux = _is_linux_os_aaz(vm)
    # pylint: disable=no-member

    # 1. be nice, figure out the default volume type and also verify VM will not be busted
    if is_linux:
        if volume_type:
            if not force and volume_type != _DATA_VOLUME_TYPE:
                raise CLIError("Only Data disks can have encryption disabled in a Linux VM. "
                               "Use '--force' to ignore the warning")
        else:
            volume_type = _DATA_VOLUME_TYPE
    elif volume_type is None:
        volume_type = _ALL_VOLUME_TYPE

    extension = vm_extension_info['Linux' if is_linux else 'Windows']
    # sequence_version should be incremented since encryptions occurred before
    sequence_version = uuid.uuid4()

    # 2. update the disk encryption extension
    # The following logic was mostly ported from xplat-cli
    public_config = {
        'VolumeType': volume_type,
        'EncryptionOperation': 'DisableEncryption',
        'SequenceVersion': str(sequence_version),
    }

    from .operations.vm_extension import VMExtensionCreate
    poller = VMExtensionCreate(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'vm_name': vm_name,
        'vm_extension_name': extension['name'],
        'location': vm['location'],
        'publisher': extension['publisher'],
        'type': extension['name'] if has_new_ade else extension['legacy_version'],
        'settings': public_config,
        'auto_upgrade_minor_version': True,
    })
    extension_result = LongRunningOperation(cmd.cli_ctx)(poller)
    if extension_result['provisioningState'] != 'Succeeded':
        raise CLIError("Extension updating didn't succeed")

    if not has_new_ade:
        # 3. Remove the secret from VM's storage profile
        from .operations.vm import VMUpdate

        class RemoveSecret(VMUpdate):
            def pre_instance_update(self, instance):
                instance.properties.storage_profile.os_disk.encryption_settings = {'enabled': False}

        LongRunningOperation(cmd.cli_ctx)(
            RemoveSecret(cli_ctx=cmd.cli_ctx)(command_args={
                'vm_name': vm_name,
                'resource_group': resource_group_name
            })
        )


def _show_vm_encryption_status_thru_new_ade(vm_instance_view):
    ade = _find_existing_ade(vm_instance_view, use_instance_view=True)
    disk_infos = []
    for div in vm_instance_view.get('instanceView', {}).get('disks', []):
        disk_infos.append({
            'name': div['name'],
            'encryptionSettings': div['encryptionSettings'],
            'statuses': [x for x in div.get('statuses', []) if x.get('code', '').startswith('EncryptionState')],
        })

    return {
        'status': ade['statuses'] if ade else None,
        'substatus': ade.get('substatuses', None) if ade else None,
        'disks': disk_infos
    }


def show_vm_encryption_status(cmd, resource_group_name, vm_name):

    encryption_status = {
        'osDisk': 'NotEncrypted',
        'osDiskEncryptionSettings': None,
        'dataDisk': 'NotEncrypted',
        'osType': None
    }
    from .operations.vm import VMShow
    vm = VMShow(cli_ctx=cmd.cli_ctx)(command_args={
        'vm_name': vm_name,
        'resource_group': resource_group_name,
        'expand': 'instanceView'
    })
    has_new_ade, has_old_ade = _detect_ade_status(vm)
    if not has_new_ade and not has_old_ade:
        logger.warning('Azure Disk Encryption is not enabled')
        return None
    if has_new_ade:
        return _show_vm_encryption_status_thru_new_ade(vm)
    is_linux = _is_linux_os_aaz(vm)

    # pylint: disable=no-member
    # The following logic was mostly ported from xplat-cli
    os_type = 'Linux' if is_linux else 'Windows'
    encryption_status['osType'] = os_type
    extension = vm_extension_info[os_type]
    from .operations.vm_extension import VMExtensionShow
    extension_result = VMExtensionShow(cli_ctx=cmd.cli_ctx)(command_args={
        'vm_name': vm_name,
        'resource_group': resource_group_name,
        'name': extension['name'],
        'expand': 'instanceView'
    })
    logger.debug(extension_result)
    if _statuses := extension_result['instanceView'].get('statuses', []):
        encryption_status['progressMessage'] = _statuses[0].message

    substatus_message = None
    if _substatuses := extension_result['instanceView'].get('substatuses', []):
        substatus_message = _substatuses[0].message

    encryption_status['osDiskEncryptionSettings'] = vm['storageProfile'].get('osDisk', {}).get('encryptionSettings', None)

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
        if (encryption_status['osDiskEncryptionSettings'] and
                bool(encryption_status['osDiskEncryptionSettings'].get('enabled', '')) and
                encryption_status['osDiskEncryptionSettings'].get('diskEncryptionKey', {}).get('secret_url', '')):
            encryption_status['osDisk'] = _STATUS_ENCRYPTED
        else:
            encryption_status['osDisk'] = 'Unknown'

        if extension_result['provisioning_state'] == 'Succeeded':
            volume_type = extension_result.get('settings', {}).get('VolumeType', None)
            about_data_disk = not volume_type or volume_type.lower() != 'os'
            if about_data_disk and extension_result.get('settings', {}).get('EncryptionOperation', None) == 'EnableEncryption':
                encryption_status['dataDisk'] = _STATUS_ENCRYPTED

    return encryption_status


def _get_keyvault_key_url(cli_ctx, keyvault_name, key_name):
    vault_base_url = get_key_vault_base_url(cli_ctx, keyvault_name)
    client = create_data_plane_keyvault_key_client(cli_ctx, vault_base_url)
    key = client.get_key(key_name)
    return key.id


def _handles_default_volume_type_for_vmss_encryption(is_linux, volume_type, force):
    if is_linux:
        volume_type = volume_type or _DATA_VOLUME_TYPE
        if volume_type != _DATA_VOLUME_TYPE:
            msg = 'OS disk encyrption is not yet supported for Linux VM scale sets'
            if force:
                logger.warning(msg)
            else:
                from knack.util import CLIError
                raise CLIError(msg)
    else:
        volume_type = volume_type or _ALL_VOLUME_TYPE
    return volume_type


def encrypt_vmss(cmd, resource_group_name, vmss_name,  # pylint: disable=too-many-locals, too-many-statements
                 disk_encryption_keyvault,
                 key_encryption_keyvault=None,
                 key_encryption_key=None,
                 key_encryption_algorithm='RSA-OAEP',
                 volume_type=None,
                 encryption_identity=None,
                 force=False):
    from azure.mgmt.core.tools import parse_resource_id
    from knack.util import CLIError

    from .aaz.latest.vmss import Update as VMSSUpdate

    class VMSSEncrypt(VMSSUpdate):
        def pre_instance_update(self, instance):
            _disk_encryption_keyvault, _key_encryption_keyvault, _key_encryption_key, _volume_type = \
                disk_encryption_keyvault, key_encryption_keyvault, key_encryption_key, volume_type

            is_linux = _is_linux_os_aaz(instance.properties.virtual_machine_profile.to_serialized_data())
            extension = vm_extension_info['Linux' if is_linux else 'Windows']

            # 1. First validate arguments
            _volume_type = _handles_default_volume_type_for_vmss_encryption(is_linux, _volume_type, force)

            # retrieve keyvault details
            _disk_encryption_keyvault_url = get_key_vault_base_url(
                cmd.cli_ctx, (parse_resource_id(_disk_encryption_keyvault))['name']
            )

            # disk encryption key itself can be further protected, so let us verify
            if _key_encryption_key:
                _key_encryption_keyvault = _key_encryption_keyvault or _disk_encryption_keyvault

            if encryption_identity:
                result = updateVmssEncryptionSetting(cmd, instance.to_serialized_data(), resource_group_name, vmss_name, encryption_identity)
                if result:
                    logger.info("Encryption Identity successfully set in virtual machine scale set")
                else:
                    raise CLIError("Failed to update encryption Identity to the VMSS")

            #  to avoid bad server errors, ensure the vault has the right configurations
            _verify_keyvault_good_for_encryption(cmd.cli_ctx, _disk_encryption_keyvault, _key_encryption_keyvault, instance.to_serialized_data(), force)

            # if key name and not key url, get url.
            if _key_encryption_key and '://' not in _key_encryption_key:
                _key_encryption_key = _get_keyvault_key_url(
                    cmd.cli_ctx, (parse_resource_id(_key_encryption_keyvault))['name'], _key_encryption_key)

            # 2. we are ready to provision/update the disk encryption extensions
            public_config = {
                'KeyVaultURL': _disk_encryption_keyvault_url,
                'KeyEncryptionKeyURL': _key_encryption_key or '',
                "KeyVaultResourceId": _disk_encryption_keyvault,
                "KekVaultResourceId": _key_encryption_keyvault if _key_encryption_key else '',
                'KeyEncryptionAlgorithm': key_encryption_algorithm if _key_encryption_key else '',
                'VolumeType': _volume_type,
                'EncryptionOperation': 'EnableEncryption'
            }

            ext = {
                'name': extension['name'],
                'properties': {
                    'publisher': extension['publisher'],
                    'type_handler_version': extension['version'],
                    'type': extension['name'],
                    'settings': public_config,
                    'auto_upgrade_minor_version': True,
                    'force_update_tag': str(uuid.uuid4())
                }
            }
            exts = [ext]

            # remove any old ade extensions set by this command and add the new one.
            vmss_ext_profile = instance.properties.virtual_machine_profile.extension_profile
            if vmss_ext_profile and vmss_ext_profile.extensions:
                exts.extend(old_ext for old_ext in instance.properties.virtual_machine_profile.extension_profile.extensions
                            if old_ext.properties.type != ext['properties']['type'] or old_ext.name != ext['name'])
            instance.properties.virtual_machine_profile.extension_profile.extensions = exts

            # Avoid unnecessary permission error
            instance.properties.virtual_machine_profile.storage_profile.image_reference = None

        def post_operations(self):
            _show_post_action_message(resource_group_name, vmss_name, self.ctx.vars.instance.properties.upgrade_policy.mode == "Manual", True)

    poller = VMSSEncrypt(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'vm_scale_set_name': vmss_name
    })
    LongRunningOperation(cmd.cli_ctx)(poller)


def decrypt_vmss(cmd, resource_group_name, vmss_name, volume_type=None, force=False):
    from .aaz.latest.vmss import Update

    class VMSSDecrypt(Update):
        def pre_instance_update(self, instance):
            is_linux = _is_linux_os_aaz(instance.properties.virtual_machine_profile.to_serialized_data())
            extension = vm_extension_info['Linux' if is_linux else 'Windows']

            # 1. be nice, figure out the default volume type
            _volume_type = _handles_default_volume_type_for_vmss_encryption(is_linux, volume_type, force)

            # 2. update the disk encryption extension
            public_config = {
                'VolumeType': _volume_type,
                'EncryptionOperation': 'DisableEncryption',
            }

            ext = {
                'name': extension['name'],
                'properties': {
                    'publisher': extension['publisher'],
                    'type_handler_version': extension['version'],
                    'type': extension['name'],
                    'settings': public_config,
                    'auto_upgrade_minor_version': True,
                    'force_update_tag': str(uuid.uuid4())
                }
            }

            ade_extension_matched = False
            for i, x in enumerate(instance.properties.virtual_machine_profile.extension_profile.extensions):
                if (str(x.name).lower() == extension['name'].lower() and
                        str(x.properties.publisher).lower() == extension['publisher'].lower()):
                    ade_extension_matched = True
                    instance.properties.virtual_machine_profile.extension_profile.extensions[i] = ext
                    break

            if not ade_extension_matched:
                from knack.util import CLIError
                raise CLIError("VM scale set '{}' was not encrypted".format(vmss_name))

            # Avoid unnecessary permission error
            instance.properties.virtual_machine_profile.storage_profile.image_reference = None

        def post_operations(self):
            _show_post_action_message(resource_group_name, vmss_name, self.ctx.vars.instance.properties.upgrade_policy.mode == "Manual", False)

    poller = VMSSDecrypt(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'vm_scale_set_name': vmss_name
    })
    LongRunningOperation(cmd.cli_ctx)(poller)


def _show_post_action_message(resource_group_name, vmss_name, maunal_mode, enable):
    msg = ''
    if maunal_mode:
        msg = ("With manual upgrade mode, you will need to run 'az vmss update-instances -g {} -n {} "
               "--instance-ids \"*\"' to propagate the change.\n".format(resource_group_name, vmss_name))
    msg += ("Note, {} encryption will take a while to finish. Please query the status using "
            "'az vmss encryption show -g {} -n {}'. For Linux VM, you will lose the access during the period".format(
                'enabling' if enable else 'disabling', resource_group_name, vmss_name))
    logger.warning(msg)


def show_vmss_encryption_status(cmd, resource_group_name, vmss_name):
    from .operations.vmss import VMSSListInstances
    vm_instances = VMSSListInstances(cli_ctx=cmd.cli_ctx)(command_args={
        'virtual_machine_scale_set_name': vmss_name,
        'resource_group': resource_group_name,
        'expand': 'instanceView',
        'select': 'instanceView'
    })

    result = []
    for instance in vm_instances:
        view = instance['instanceView']
        disk_infos = []
        vm_enc_info = {
            'id': instance['id'],
            'disks': disk_infos
        }
        for div in view['disks']:
            disk_infos.append({
                'name': div['name'],
                'encryptionSettings': div.get('encryptionSettings', []),
                'statuses': [x for x in (div.get('statuses', [])) if (x.get('code', '')).startswith('EncryptionState')]
            })

        result.append(vm_enc_info)
    return result


# aaz implementation
def _verify_keyvault_good_for_encryption(cli_ctx, disk_vault_id, key_vault_id, vm_or_vmss, force):
    def _report_client_side_validation_error(msg):
        if force:
            logger.warning("WARNING: %s %s", msg, "Encryption might fail.")
        else:
            from knack.util import CLIError
            raise CLIError("ERROR: {}".format(msg))

    resource_type = "VMSS" if vm_or_vmss['type'].lower().endswith("virtualmachinescalesets") else "VM"

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    from azure.mgmt.core.tools import parse_resource_id

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT).vaults
    disk_vault_resource_info = parse_resource_id(disk_vault_id)
    key_vault = client.get(disk_vault_resource_info['resource_group'], disk_vault_resource_info['name'])

    # ensure vault has 'EnabledForDiskEncryption' permission or VM has encryption identity set for ADE operation
    if resource_type == 'VM':
        vm_encryption_identity = vm_or_vmss
    else:
        vm_encryption_identity = vm_or_vmss['properties']['virtualMachineProfile']

    if vm_encryption_identity.get('securityProfile', {}).get('encryptionIdentity', {}).get('userAssignedIdentityResourceId', None):
        pass
    elif not key_vault.properties or not key_vault.properties.enabled_for_disk_encryption:
        _report_client_side_validation_error(
            "Keyvault '{}' is not enabled for disk encryption.".format(disk_vault_resource_info['resource_name']))

    if key_vault_id:
        kek_vault_info = parse_resource_id(key_vault_id)
        if disk_vault_resource_info['name'].lower() != kek_vault_info['name'].lower():
            client.get(kek_vault_info['resource_group'], kek_vault_info['name'])

    # verify subscription mataches
    vm_vmss_resource_info = parse_resource_id(vm_or_vmss['id'])
    if vm_vmss_resource_info['subscription'].lower() != disk_vault_resource_info['subscription'].lower():
        _report_client_side_validation_error("{} {}'s subscription does not match keyvault's subscription."
                                             .format(resource_type, vm_vmss_resource_info['name']))

    # verify region matches
    if key_vault.location.replace(' ', '').lower() != vm_or_vmss['location'].replace(' ', '').lower():
        _report_client_side_validation_error(
            "{} {}'s region does not match keyvault's region.".format(resource_type, vm_vmss_resource_info['name']))
