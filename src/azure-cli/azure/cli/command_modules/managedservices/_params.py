# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_three_state_flag


def load_arguments(self, _):

    for item in ['managedservices definition show', 'managedservices definition delete']:
        with self.argument_context(item) as c:
            c.argument('definition', help='The identifier (guid) or the fully qualified resource id of the registration definition. When resource id is used, subscription id and resource group parameters are ignored.')

    for item in ['managedservices assignment list', 'managedservices assignment show']:
        with self.argument_context(item) as c:
            c.argument('include_definition', arg_type=get_three_state_flag(),
                       help='When provided, gets the associated registration definition details.')

    for item in ['managedservices assignment show', 'managedservices assignment delete']:
        with self.argument_context(item) as c:
            c.argument('assignment',
                       help='The identifier (guid) or the fully qualified resource id of the registration assignment. When resource id is used, subscription id and resource group parameters are ignored.')
