from azure.cli.core._util import CLIError
from .custom import get_vm, set_vm, _compute_client_factory

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

def keyvault_client_factory(**_): #TODO add dependencies
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.keyvault import KeyVaultManagementClient
    return get_mgmt_service_client(KeyVaultManagementClient)

def encrypt_disk(resource_group_name, vm_name,
                 aad_client_id, aad_client_secret, #  TODO: client_cert_thumbprint, 
                 keyvault, key_encryption_key_url=None, key_encryption_vault_id=None, client_cert_thumbprint=None,
                 volume_type='ALL', sequence_version=None,  # TODO warn if is missing 
                 key_encryption_algorithm='RSA-OAEP'):
    from msrestazure.azure_exceptions import CloudError

    vm = get_vm(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = os_type.lower() == 'linux'
    extension = extension_info[os_type]
    # TODO: support passphase for linux
    # TODO: check volume_type
    # TODO: cross check the secret stuff
    compute_client = _compute_client_factory()
    if sequence_version is None:
        try:
            compute_client.virtual_machine_extensions.get(resource_group_name, vm_name, extension['name'])
            raise CLIError("Please supply 'sequence_number' as disk-encryption operation was performed on the same VM")
        except CloudError:
            pass

    keyvault_client = keyvault_client_factory()
    from azure.cli.core.commands.arm import parse_resource_id, is_valid_resource_id
    if is_valid_resource_id(keyvault):
        res =  parse_resource_id(keyvault)
        keyvault_info = keyvault_client.vaults.get(res['resource_group'], res['name'])
    else:
        keyvault_info = keyvault_client.vaults.get(resource_group_name, keyvault)
    keyvault_url = keyvault_info.properties.vault_uri

    public_config = {
        'AADClientID': aad_client_id,
        'AADClientCertThumbprint': client_cert_thumbprint,
        'KeyVaultURL': keyvault_url,
        'VolumeType': volume_type,
        'EncryptionOperation': 'EnableEncryption',
        'KeyEncryptionKeyURL': key_encryption_key_url,
        'KeyEncryptionAlgorithm': key_encryption_algorithm, # TODO cross check
        'SequenceVersion': sequence_version,
        }
    private_config = { 'AADClientSecret': aad_client_secret if is_linux else (aad_client_secret or '') }

    # If keyEncryptionKeyUrl is not null but keyEncryptionAlgorithm is, use the default key encryption algorithm
    #if(!utils.stringIsNullOrEmpty(options.keyEncryptionKeyUrl)) {
    #    if(utils.stringIsNullOrEmpty(options.keyEncryptionAlgorithm)) {
    #        params.keyEncryptionAlgorithm = vmConstants.EXTENSIONS.DEFAULT_KEY_ENCRYPTION_ALGORITHM;
    #    }
    #}

    from azure.mgmt.compute.models import VirtualMachineExtension, DiskEncryptionSettings, KeyVaultSecretReference, KeyVaultKeyReference, SubResource

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
                                  publisher=extension['publisher'],
                                  virtual_machine_extension_type=extension['name'],
                                  protected_settings=private_config,
                                  type_handler_version=extension['version'],
                                  settings=public_config,
                                  auto_upgrade_minor_version=True)

    poller = compute_client.virtual_machine_extensions.create_or_update(resource_group_name, vm_name,
                                                       extension['name'], ext)
    temp = poller.result()

    extension_result = compute_client.virtual_machine_extensions.get(resource_group_name, vm_name, extension['name'], 'instanceView')
    #TODO check the result
    status_url = extension_result.instance_view.statuses[0].message
    #TODO check the status_url

    vm = get_vm(resource_group_name, vm_name)
    disk_encryption_settings = DiskEncryptionSettings(disk_encryption_key=KeyVaultSecretReference(secret_url=status_url, source_vault=SubResource(keyvault_info.id)), 
                                                      key_encryption_key=None, # TODO key_encryption_key_url,
                                                      enabled = True)
    #Cross check the xplat's stuff

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)

def disable_disk_encryption(resource_group_name, vm_name, sequence_version, volume_type='DATA'):
    #// +---------+---------------+----------------------------+ 
    #// | OSType  |  VolumeType   | UpdateVmEncryptionSettings | 
    #// +---------+---------------+----------------------------+ 
    #// | Windows | OS            | Yes                        | 
    #// | Windows | Data          | No                         | 
    #// | Windows | Not Specified | Yes                        | 
    #// | Linux   | OS            | N/A                        | 
    #// | Linux   | Data          | Yes                        | 
    #// | Linux   | Not Specified | N/A                        | 
    #// +---------+---------------+----------------------------+ 
    vm = get_vm(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = os_type.lower() == 'linux'
    if is_linux and volume_type != 'DATA':
        raise CLIError("Disabling encryption other than 'DATA' disks is not supported on Linux VM")
    extension = extension_info[os_type]

    public_config = {
        'VolumeType': volume_type,
        'EncryptionOperation': 'DisableEncryption',
        'SequenceVersion': sequence_version,
    }

    from azure.mgmt.compute.models import VirtualMachineExtension, DiskEncryptionSettings, KeyVaultSecretReference, KeyVaultKeyReference, SubResource

    ext = VirtualMachineExtension(vm.location,  # pylint: disable=no-member
                                  publisher=extension['publisher'],
                                  virtual_machine_extension_type=extension['name'],
                                  type_handler_version=extension['version'],
                                  settings=public_config,
                                  auto_upgrade_minor_version=True)

    client = _compute_client_factory()
    poller = client.virtual_machine_extensions.create_or_update(resource_group_name, vm_name,
                                                       extension['name'], ext)
    temp = poller.result()

    extension_result = client.virtual_machine_extensions.get(resource_group_name, vm_name, extension['name'], 'instanceView')
    #TODO check the result
    status_url = extension_result.instance_view.statuses[0].message
    #TODO check the status_url

    vm = get_vm(resource_group_name, vm_name)
    disk_encryption_settings = DiskEncryptionSettings(enabled = False)
    #Cross check the xplat's stuff

    vm.storage_profile.os_disk.encryption_settings = disk_encryption_settings
    return set_vm(vm)

def show_disk_encryption(resource_group_name, vm_name):
    vm = get_vm(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type.value
    is_linux = os_type.lower() == 'linux'
    extension = extension_info[os_type]
    client = _compute_client_factory()
    extension_result = client.virtual_machine_extensions.get(resource_group_name, vm_name, extension['name'], 'instanceView')
    return extension_result