#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# This replaces the existing AzureOperationPoller.__init__ implementation with a custom
# implemenatation that sets the daemon property on the created thread to True. This
# allows the program to exit when Ctrl+C is pressed, without having to press it again
# to kill the running thread.
from msrestazure.azure_operation import AzureOperationPoller

# pylint: disable=protected-access
def azureOperationPollerInit(self, send_cmd, output_cmd, update_cmd, timeout=30):
    import threading
    self._timeout = timeout
    self._response = None
    self._operation = None
    self._exception = None
    self._callbacks = []
    self._done = threading.Event()
    self._thread = threading.Thread(
        target=self._start, args=(send_cmd, update_cmd, output_cmd))
    # Need this set to True so Ctrl+C will simply exit
    self._thread.daemon = True
    self._thread.start()
AzureOperationPoller.__init__ = azureOperationPollerInit
