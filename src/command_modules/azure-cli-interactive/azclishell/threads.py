# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading


# class ContinuousPingThread(threading.Thread):
#     """ thread to keep the progress indications running """
#     def __init__(self, target, args):
#         super(ContinuousPingThread, self).__init__()
#         self.target = target
#         self.args = args

#     def run(self):
#         import time
#         try:
#             while True:
#                 if self.target(self.args):
#                 # if super(ContinuousPingThread, self).run():
#                     time.sleep(4)
#                     break
#                 time.sleep(.25)
#         except KeyboardInterrupt:
#             pass


class LoadCommandTableThread(threading.Thread):
    """ a thread that loads the command table """
    def __init__(self, target, shell):
        super(LoadCommandTableThread, self).__init__()
        self.initialize_function = target
        self.shell = shell
        self.daemon = True

    def run(self):
        from azclishell._dump_commands import FRESH_TABLE
        from azclishell.az_completer import initialize_command_table_attributes

        try:
            FRESH_TABLE.dump_command_table()
        except KeyboardInterrupt:
            pass
        self.initialize_function(self.shell)
        initialize_command_table_attributes(self.shell.completer)
