# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from knack.arguments import CLIArgumentType

def load_arguments(self, _):

    from azure.cli.core.commands.parameters import resource_group_name_type, tags_type

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')

    #region Service

    with self.argument_context('dms') as c:
        c.argument('service_name', name_arg_type, help='The name of the Service')
        c.argument('group_name', resource_group_name_type)
        c.argument('tags', tags_type)

    #endregion