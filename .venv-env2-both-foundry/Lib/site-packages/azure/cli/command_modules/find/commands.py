# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    with self.command_group('') as g:
        g.custom_command('find', 'process_query', is_preview=False)
    return self.command_table
