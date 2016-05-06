import argparse

from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration
from azure.mgmt.compute.models import VirtualHardDisk

from azure.cli.commands import (COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, extend_parameter,
                                patch_aliases)
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.command_modules.vm._validators import MinMaxValue
from azure.cli.command_modules.vm._actions import VMImageFieldAction, VMSSHFieldAction
from azure.cli._help_files import helps
from azure.cli._locale import L

# FACTORIES

def _compute_client_factory(**_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'diskname': {
        'name': '--name -n',
        'help': L('Disk name'),
    },
    'disksize': {
        'name': '--disksize',
        'help': L('Size of disk (Gb)'),
        'type': MinMaxValue(1, 1023),
        'default': 1023
    },
    'image_location': {
        'name': '--image-location',
        'help': L('Image location')
    },
    'lun': {
        'name': '--lun',
        'help': L('0-based logical unit number (LUN). Max value depends on the Virtual ' + \
                  'Machine size'),
        'type': int,
    },
    'vhd': {
        'name': '--vhd',
        'type': VirtualHardDisk
    },
    'vm_name': {
        'name': '--vm-name',
        'dest': 'vm_name',
        'help': 'Name of Virtual Machine to update',
    }
})

VM_CREATE_PARAMETER_ALIASES = {
    'name': {
        'name': '--name -n'
    },
    'os_disk_uri': {
        'name': '--os-disk-uri',
        'help': argparse.SUPPRESS
    },
    'os_offer': {
        'name': '--os_offer',
        'help': argparse.SUPPRESS
    },
    'os_publisher': {
        'name': '--os-publisher',
        'help': argparse.SUPPRESS
    },
    'os_sku': {
        'name': '--os-sku',
        'help': argparse.SUPPRESS
    },
    'os_type': {
        'name': '--os-type',
        'help': argparse.SUPPRESS
    },
    'os_version': {
        'name': '--os-version',
        'help': argparse.SUPPRESS
    },
}

# EXTRA PARAMETER SETS

VM_CREATE_EXTRA_PARAMETERS = {
    'image': {
        'name': '--image',
        'help': 'The OS image.  Supported values: Common OS (e.g. Win2012R2Datacenter), ' + \
                'URN (e.g. "publisher:offer:sku:version"), or existing VHD URI.',
        'action': VMImageFieldAction
    },
    'ssh_key_value': {
        'name': '--ssh-key-value',
        'action': VMSSHFieldAction
    }
}

VM_PATCH_EXTRA_PARAMETERS = {
    'resource_group_name':
        extend_parameter(PARAMETER_ALIASES['resource_group_name'], required=True),
    'vm_name':
        extend_parameter(PARAMETER_ALIASES['vm_name'], required=True)
}

# HELP PARAMETERS

helps['vm create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-quick-create-cli/ for an end-to-end tutorial
            parameters: 
                - name: --image
                  type: string
                  required: false
                  short-summary: OS image
                  long-summary: |
                    Common OS types: CentOS, CoreOS, Debian, openSUSE, RHEL, SLES, UbuntuLTS,
                    Win2012R2Datacenter, Win2012Datacenter, Win2008R2SP1
                    Example URN: canonical:Ubuntu_Snappy_Core:15.04:2016.0318.1949
                    Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd
                  populator-commands: 
                    - az vm image list
                    - az vm image show
            examples:
                - name: Create a simple Windows Server VM with private IP address
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create --image canonical:Ubuntu_Snappy_Core:15.04:2016.0318.1949
                    --admin-username myadmin --admin-password Admin_001 --authentication-type sshkey
                    --virtual-network-type existing --virtual-network-name myvnet --subnet-name default
                    --availability-set-type existing --availability-set-id myavailset
                    --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                    -l "West US" -g myvms --name myvm18o --ssh-key-value "<ssh-rsa-key or key-file-path>"
            """
