# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading


class ProgressViewThread(threading.Thread):
    """ thread to keep the progress indications running """
    def __init__(self, func, arg):
        super(ProgressViewThread, self).__init__()
        self.func = func
        self.arg = arg

    def run(self):
        import time
        try:
            while True:
                if self.func(self.arg):
                    time.sleep(4)
                    break
                time.sleep(.25)
        except KeyboardInterrupt:
            pass


class LoadCommandTableThread(threading.Thread):
    """ a thread that loads the command table """
    def __init__(self, func, arg):
        super(LoadCommandTableThread, self).__init__()
        self.daemon = True
        self.arg = arg
        self.func = func

    def run(self):
        from azclishell._dump_commands import FRESH_TABLE
        from azclishell.az_completer import initialize_command_table_attributes

        try:
            FRESH_TABLE.dump_command_table()
        except KeyboardInterrupt:
            pass
        self.func(self.arg)
        initialize_command_table_attributes(self.arg.completer)
