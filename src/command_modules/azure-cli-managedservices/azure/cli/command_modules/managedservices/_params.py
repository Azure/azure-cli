# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_resource_name_completion_list


def load_arguments(self, _):
    with self.argument_context('managedservices definitions') as c:
        c.argument('name_or_id', id_part='child_name_1',
                   help='The registration definition name or the fully qualified resource id.')

    with self.argument_context('managedservices definitions show') as c:
        c.argument('name_or_id', id_part='child_name_1',
                   help='The registration definition name or the fully qualified resource id.')

    with self.argument_context('managedservices definitions create') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the registration definition.',
                   completer=get_resource_name_completion_list('Microsoft.ManagedServices/registrationDefinitions'))

    with self.argument_context('managedservices definitions list') as c:
        c.argument('registration_definition_id', id_part=None)

    with self.argument_context('managedservices assignments') as c:
        c.argument('name_or_id', id_part='child_name_1',
                   help='The registration assignment name or the fully qualified resource id.')
