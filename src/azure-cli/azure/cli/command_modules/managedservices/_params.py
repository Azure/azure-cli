# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_resource_name_completion_list
from azure.cli.core.commands.parameters import get_three_state_flag
from azure.cli.core.api import get_subscription_id_list

def load_arguments(self, _):

    # with self.argument_context('managedservices') as c:
    #     c.ignore('subscription')
            
    # with self.argument_context('managedservices definition show') as c:
    #     c.argument('definition', id_part='child_name_1',
    #                help='The registration definition name or the fully qualified resource id.')

    # with self.argument_context('managedservices definition create') as c:
    #     c.argument('name', options_list=['--name', '-n'], help='Name of the registration definition.',
    #                completer=get_resource_name_completion_list('Microsoft.ManagedServices/registrationDefinitions'))

    # with self.argument_context('managedservices definition list') as c:
    #     c.argument('definition_id', id_part=None)

    # with self.argument_context('managedservices definition assignment') as c:
    #     c.argument('assignment', id_part='child_name_1',
    #                help='The registration assignment name or the fully qualified resource id.')
       
    group_name = 'ManagedServices'
    with self.argument_context('managedservices definition') as c:
        c.argument('api_version', arg_group=group_name, help='The API Version to target.') #this works

    for item in ['managedservices definition show', 'managedservices definition delete']:
        with self.argument_context(item) as c:
            c.argument('definition', help='The identifier (guid) or the fully qualified resource id of the registration definition. When resource id is used, subscription id and resource group parameters are ignored.')

    for item in ['managedservices assignment list', 'managedservices assignment show']:
        with self.argument_context(item) as c:
            c.argument('include_definition', arg_type=get_three_state_flag(), 
                   help='When provided, gets the associated registration definition details.')
