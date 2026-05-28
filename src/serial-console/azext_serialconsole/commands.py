# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):

    with self.command_group('serial-console') as g:
        g.custom_command('connect', 'connect_serialconsole')
        g.custom_command('enable', 'enable_serialconsole')
        g.custom_command('disable', 'disable_serialconsole')

    with self.command_group('serial-console send') as g:
        g.custom_command('nmi', 'send_nmi_serialconsole')
        g.custom_command('reset', 'send_reset_serialconsole')
        g.custom_command('sysrq', 'send_sysrq_serialconsole')
