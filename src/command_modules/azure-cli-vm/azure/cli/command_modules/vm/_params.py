from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration
from azure.mgmt.compute.models import VirtualHardDisk

from azure.cli.commands import (COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, extend_parameter)
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli._locale import L
from azure.cli.command_modules.vm._validators import MinMaxValue

# FACTORIES

def _compute_client_factory(**_):
    return get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'diskname': {
        'name': '--name -n',
        'dest': 'name',
        'help': L('Disk name'),
    },
    'disksize': {
        'name': '--disksize',
        'dest': 'disksize',
        'help': L('Size of disk (Gb)'),
        'type': MinMaxValue(1, 1023),
        'default': 1023
    },
    'lun': {
        'name': '--lun',
        'dest': 'lun',
        'help': L('0-based logical unit number (LUN). Max value depends on the Virtual ' + \
                  'Machine size'),
        'type': int,
    },
    'vhd': {
        'name': '--vhd',
        'type': VirtualHardDisk
    },
})
