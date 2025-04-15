# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import threading
import uuid

from azure.core.exceptions import AzureError, HttpResponseError
from azure.core.polling import NoPolling
from azure.core.polling.base_polling import LROBasePolling
from azure.core.tracing.common import with_current_context
from azure.core.tracing.decorator import distributed_trace
# import requests in main thread to resolve import deadlock between threads in python
# reference https://github.com/psf/requests/issues/2925 and https://github.com/Azure/azure-cli/issues/26272
import requests  # pylint: disable=unused-import

_LOGGER = logging.getLogger(__name__)


class AAZNoPolling(NoPolling):
    pass


class AAZBasePolling(LROBasePolling):

    def __init__(self, *args, http_response_error_callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._http_response_error_callback = http_response_error_callback

    def initialize(self, client, initial_response, deserialization_callback):
        try:
            super().initialize(client, initial_response, deserialization_callback)
        except HttpResponseError as err:
            if self._http_response_error_callback:
                # the HttpResponseError raise by LROBasePolling missing detailed error message
                # _http_response_error_callback will build HttpResponseError with detailed error message
                self._http_response_error_callback(err.response)
            else:
                raise err

    def run(self):
        try:
            super().run()
        except HttpResponseError as err:
            if self._http_response_error_callback:
                # the HttpResponseError raise by LROBasePolling missing detailed message
                # _http_response_error_callback will build HttpResponseError with detailed error message
                self._http_response_error_callback(err.response)
            else:
                raise err


class AAZLROPoller:

    def __init__(self, polling_generator, result_callback):
        self._callbacks = []
        self._polling_generator = polling_generator  # generator
        self._polling_method = None
        self._result_callback = result_callback

        # Prepare thread execution
        self._thread = None
        self._done = None
        self._exception = None

        self._done = threading.Event()
        self._thread = threading.Thread(
            target=with_current_context(self._start),
            name="AAZLROPoller({})".format(uuid.uuid4()))
        self._thread.daemon = True
        self._thread.start()

    def _start(self):
        """Start the long running operation.
        On completion, runs any callbacks.

        :param callable update_cmd: The API request to check the status of
         the operation.
        """
        try:
            for polling_method in self._polling_generator:
                self._polling_method = polling_method
                try:
                    self._polling_method.run()
                except AzureError as error:
                    if not error.continuation_token:
                        try:
                            error.continuation_token = self._polling_method.get_continuation_token()
                        except Exception as err:  # pylint: disable=broad-except
                            _LOGGER.warning("Unable to retrieve continuation token: %s", err)
                            error.continuation_token = None
                    raise error
        except Exception as error:  # pylint: disable=broad-except
            self._exception = error
        finally:
            self._done.set()

    def result(self, timeout=None):
        """Return the result of the long running operation, or
        the result available after the specified timeout.

        :returns: The deserialized resource of the long running operation,
         if one is available.
        :raises ~azure.core.exceptions.HttpResponseError: Server problem with the query.
        """
        self.wait(timeout)
        resource = self._polling_method.resource()
        if self._result_callback:
            return self._result_callback(resource)
        return resource

    @distributed_trace
    def wait(self, timeout=None):
        """Wait on the long running operation for a specified length
        of time. You can check if this call as ended with timeout with the
        "done()" method.

        :param float timeout: Period of time to wait for the long running
         operation to complete (in seconds).
        :raises ~azure.core.exceptions.HttpResponseError: Server problem with the query.
        """
        if self._thread is None:
            return

        self._thread.join(timeout=timeout)

        if self._exception:  # derive from BaseException
            raise self._exception

    def done(self):
        """Check status of the long running operation.

        :returns: 'True' if the process has completed, else 'False'.
        :rtype: bool
        """
        return self._thread is None or not self._thread.is_alive()
