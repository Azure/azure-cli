# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def load_command_table(self, _):

    with self.command_group('component') as g:
        g.custom_command('list', 'list_components')
        g.custom_command('update', 'update')
        g.custom_command('remove', 'remove')
        g.custom_command('list-available', 'list_available_components')
