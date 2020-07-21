# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_arguments(self, _):
    with self.argument_context('config') as c:
        c.argument('local', action='store_true', help='Include the local configuration in addition to the global configuration.')

        c.ignore('_subscription')  # ignore the global subscription param
    with self.argument_context('config set') as c:
        c.positional('key_value', nargs='+', help="Space-separated configurations in the form of <section>.<key>=<value>.")

    with self.argument_context('config get') as c:
        c.positional('key', nargs='?', help='The configuration to get. '
                                            'If not provided, all sections and configurations will be listed. '
                                            'If `section` is provided, all configurations under the specified section will be listed. '
                                            'If `<section>.<key>` is provided, only the corresponding configuration is shown.')

    with self.argument_context('config unset') as c:
        c.positional('key', nargs='+', help='The configuration to unset, in the form of <section>.<key>.')
