# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def load_command_table(self, _):
    # Azure Local Migration Commands
    with self.command_group('migrate local') as g:
        g.custom_command('get-protected-item', 'get_protected_item')
       

