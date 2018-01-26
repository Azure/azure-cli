# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import name_type

def load_arguments(self, _):

    with self.argument_context('example') as c:
        c.argument('example_name', arg_type=name_type, help='The name of the example.')
