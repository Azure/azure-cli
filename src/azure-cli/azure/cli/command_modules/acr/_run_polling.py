# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import time

from azure.core.polling import PollingMethod, LROPoller
from azure.core.exceptions import HttpResponseError

from ._constants import get_finished_run_status, get_succeeded_run_status


def get_run_with_polling(client,
                         run_id,
                         registry_name,
                         resource_group_name):
    from azure.mgmt.containerregistrytasks.models import Run

    def deserialize_run(response):
        return Run(json.loads(response.http_response.text()))

    return LROPoller(
        client=client,
        initial_response=client.get(
            resource_group_name, registry_name, run_id, cls=lambda x, y, z: x),
        deserialization_callback=deserialize_run,
        polling_method=RunPolling(
            registry_name=registry_name,
            run_id=run_id
        ))


class RunPolling(PollingMethod):  # pylint: disable=too-many-instance-attributes

    def __init__(self, registry_name, run_id, timeout=30):
        self._registry_name = registry_name
        self._run_id = run_id
        self._timeout = timeout
        self._client = None
        self._response = None  # Will hold latest received response
        self._url = None  # The URL used to get the run
        self.operation_status = ""
        self.operation_result = None

    def initialize(self, client, initial_response, deserialization_callback):
        self._client = client._client  # pylint: disable=protected-access
        self._response = initial_response
        self._url = initial_response.http_request.url

        self._set_operation_status(initial_response)

    def run(self):
        while not self.finished():
            time.sleep(self._timeout)
            self._update_status()

        if self.operation_status not in get_succeeded_run_status():
            from knack.util import CLIError
            raise CLIError("The run with ID '{}' finished with unsuccessful status '{}'. "
                           "Show run details by 'az acr task show-run -r {} --run-id {}'. "
                           "Show run logs by 'az acr task logs -r {} --run-id {}'.".format(
                               self._run_id,
                               self.operation_status,
                               self._registry_name,
                               self._run_id,
                               self._registry_name,
                               self._run_id
                           ))

    def status(self):
        return self.operation_status

    def finished(self):
        return self.operation_status in get_finished_run_status()

    def resource(self):
        return self.operation_result

    def _set_operation_status(self, response):
        from azure.mgmt.containerregistrytasks.models import Run, RunStatus
        if response.http_response.status_code == 200:
            self.operation_result = Run(json.loads(response.http_response.text()))
            self.operation_status = self.operation_result.status or RunStatus.queued.value
            return
        raise HttpResponseError(response)

    def _update_status(self):
        self._response = self._client._pipeline.run(  # pylint: disable=protected-access
            self._client.get(self._url), stream=False)
        self._set_operation_status(self._response)
