# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading


class LoadCommandTableThread(threading.Thread):
    """ a thread that loads the command table """
    def __init__(self, target, shell):
        super(LoadCommandTableThread, self).__init__()
        self.initialize_function = target
        self.shell = shell
        self.daemon = True

    def run(self):
        from azclishell._dump_commands import LoadFreshTable
        from azclishell.az_completer import initialize_command_table_attributes

        try:
            LoadFreshTable(self.shell).dump_command_table(self.shell)
        except KeyboardInterrupt:
            pass
        self.initialize_function(self.shell)
        initialize_command_table_attributes(self.shell.completer)
