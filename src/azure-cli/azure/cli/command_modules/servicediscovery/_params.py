# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import get_enum_type
from .action import MetaDataAction

def load_arguments(self, _):
    with self.argument_context('discovery') as c:
        c.argument('registry', help='Service registry name', default='mvpdemo')
        c.argument('ns_name', options_list=['--namespace', '--ns'], help='Namespace name registered to the registry')
        c.argument('service', help='Service name registered to the namespace')
        c.argument('protocol', help='The protocol of the service', arg_type=get_enum_type(['HTTP', 'TCP', 'DB']))
        c.argument('instance', help='Instance name registered to the service')
        c.argument('address', help='Address of the registered service instance')
        c.argument('port', help='Port of the registered service instance')
        c.argument('metadata', help='Service instance metadata. --medata key1=val1 key2=val2', nargs='*', action=MetaDataAction)
        c.argument('connection_string', options_list=['--conn-string'], help='Connection string of a database')

    for cmd_group_name in ['namespace', 'service', 'instance']:
        with self.argument_context('discovery {}'.format(cmd_group_name)) as c:
            c.argument('description', options_list=['--description, --desc'], help='Description of the {}'.format(cmd_group_name))
    
    with self.argument_context('discovery namespace create') as c:
        c.argument('app_config', help='Name of an Azure App Config service. The registered intances will be automatically exported to the app config if the parameter is set')
    with self.argument_context('discovery namespace export') as c:
        c.argument('app_config', help='Name an Azure App Config service. The registered intances will be exported to the app config')