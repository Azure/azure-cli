# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import get_location_type, tags_type, get_enum_type

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME',
                                help='The name of the identity resource.')


def load_arguments(self, _):

    with self.argument_context('identity') as c:
        c.argument('resource_name', arg_type=name_arg_type, id_part='name')

    with self.argument_context('identity create') as c:
        c.argument('location', get_location_type(self.cli_ctx), required=False)
        c.argument('tags', tags_type)
        c.argument('assignment_restriction', required=False, help='Identity assignment restriction, used to restrict the resources that can be assigned to the identity.')

    with self.argument_context('identity update') as c:
        c.argument('tags', tags_type)
        c.argument('assignment_restriction', required=False, help='Identity assignment restriction, used to restrict the resources that can be assigned to the identity.')
