# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading

from azclishell._dump_commands import DUMP_TABLE


class ExecuteThread(threading.Thread):
    """ thread for executing commands """
    def __init__(self, func, args):
        super(ExecuteThread, self).__init__()
        self.args = args
        self.func = func

    def run(self):
        self.func(self.args)


class ProgressViewThread(threading.Thread):
    """ thread to keep the toolbar spinner spinning """
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
        try:
            DUMP_TABLE.dump_command_table()
        except KeyboardInterrupt:
            pass
        self.func(self.arg)
