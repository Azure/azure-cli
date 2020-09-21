# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_arguments(self, _):
    with self.argument_context('config') as c:
        c.ignore('_subscription')  # ignore the global subscription param

    with self.argument_context('config set') as c:
        c.positional('key_value_pairs', nargs='+',
                     help="Set options in the form of <section>.<name>=<value>. "
                          "If `<section>` is omitted, `core` will be used. "
                          "To set multiple options, separate each key value pair with spaces.")
        c.argument('local', action='store_true', help='Set as a local configuration in the working directory.')

    with self.argument_context('config get') as c:
        c.positional('key', nargs='?',
                     help='The configuration to get. '
                          'To list all options under all sections, leave it unspecified. '
                          'To list all options under a section, use `<section>.`. '
                          'To list one option, use `<section>.<name>`. If `<section>` is omitted, `core` will be used. ')
        c.argument('local', action='store_true',
                   help='Include local configuration. Scan from the working directory up to the root drive, then the global configuration '
                        'and return the first occurrence.')

    with self.argument_context('config unset') as c:
        c.positional('keys', nargs='+',
                     help='The configuration to unset, in the form of `<section>.<name>`. '
                          'If `<section>` is omitted, `core` will be used. '
                          'To unset multiple options, separate each key with spaces.')
        c.argument('local', action='store_true',
                   help='Include local configuration. Scan from the working directory up to the root drive, then the global configuration '
                        'and unset the first occurrence.')

    with self.argument_context('config param-persist show') as c:
        c.positional('name', nargs='*', help='Space-separated list of parameter persistence names.')

    with self.argument_context('config param-persist delete') as c:
        c.positional('name', nargs='*', help='Space-separated list of parameter persistence names. Either positional name argument or --all can be specified.')
        c.argument('all', help='Clear all parameter persistence data. Either positional name argument  or --all can be specified.', action='store_true')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation. Only available when --all is specified.', action='store_true')
        c.argument('purge', help='Delete parameter persistence file from working directory. Only available when --all is specified.', action='store_true')
        c.argument('recursive', help='Indicate this is recursive delete of parameter persistence. Only available when --all is specified.', action='store_true')
