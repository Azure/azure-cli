# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_arguments(self, _):

    with self.argument_context('config set') as c:
        c.positional('key_value', nargs='+', help="Space-separated configurations in the form of [section].[key]=[value].")
        c.argument('local', action='store_true', help='Use the local config')
        c.ignore('_subscription')  # ignore the global subscription param

    with self.argument_context('config get') as c:
        c.positional('key', nargs='?', help='The configuration in the form of [section].[key]=[value].')
        c.argument('local', action='store_true', help='Use the local config')
        c.ignore('_subscription')  # ignore the global subscription param

    with self.argument_context('config unset') as c:
        c.positional('key', nargs='+', help='The configuration in the form of [section].[key]=[value].')
        c.argument('local', action='store_true', help='Use the local config')
        c.ignore('_subscription')  # ignore the global subscription param
