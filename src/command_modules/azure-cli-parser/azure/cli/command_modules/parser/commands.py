# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long


def load_command_table(self, _):

    with self.command_group('parser') as g:
        g.custom_command('yaml', 'parse_yaml')


