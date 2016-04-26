from os import environ

from azure.mgmt.compute.models import DataDisk, VirtualHardDisk

from azure.cli.commands import (COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, extend_parameter)
from azure.cli._locale import L
from azure.cli.command_modules.vm._validators import MinMaxValue

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'diskname': {
        'name': '--diskname',
        'dest': 'name',
        'help': L('Disk name'),
        'required': True
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
        'help': L('0-based logical unit number (LUN). Max value depend on the Virtual Machine size'),
        'type': int,
        'required': True
    },
    'optional_resource_group_name':
        extend_parameter(GLOBAL_COMMON_PARAMETERS['resource_group_name'], required=False),
    'vhd': {
        'name': '--vhd',
        'required': True,
        'type': VirtualHardDisk
    },
})
