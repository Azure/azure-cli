# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

def load_command_table(self, _):

    ams_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.custom#{}'
    )
    
    with self.command_group('ams', ams_custom) as g:        
        g.command('create', 'create_mediaservice')