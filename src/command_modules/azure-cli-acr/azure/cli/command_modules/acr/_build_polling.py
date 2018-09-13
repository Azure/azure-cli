# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from msrest import Deserializer
from msrest.polling import PollingMethod, LROPoller
from msrestazure.azure_exceptions import CloudError

from azure.mgmt.containerregistry.v2018_02_01_preview import models


FINISHED = frozenset([
    models.BuildStatus.succeeded.value,
    models.BuildStatus.failed.value,
    models.BuildStatus.canceled.value,
    models.BuildStatus.error.value,
    models.BuildStatus.timeout.value])

SUCCEEDED = frozenset([models.BuildStatus.succeeded.value])

DESERIALIZER = Deserializer({k: v for k, v in models.__dict__.items() if isinstance(v, type)})


def deserialize_build(response):
    return DESERIALIZER('Build', response)


def get_build_with_polling(client,  # cf_acr_builds
                           build_id,
                           registry_name,
                           resource_group_name):
    return LROPoller(
        client=client,
        initial_response=client.get(resource_group_name, registry_name, build_id, raw=True),
        deserialization_callback=deserialize_build,
        polling_method=BuildPolling(
            registry_name=registry_name,
            build_id=build_id
        ))


class BuildPolling(PollingMethod):  # pylint: disable=too-many-instance-attributes

    def __init__(self, registry_name, build_id, timeout=15):
        self._registry_name = registry_name
        self._build_id = build_id
        self._timeout = timeout
        self._client = None  # cf_acr_builds
        self._response = None  # Will hold latest received response
        self._url = None  # The URL used to get the build
        self._deserialize = None  # The deserializer for build
        self.operation_status = ""
        self.operation_result = None

    def initialize(self, client, initial_response, deserialization_callback):
        self._client = client
        self._response = initial_response
        self._url = initial_response.request.url
        self._deserialize = deserialization_callback

        self._set_operation_status(initial_response)

    def run(self):
        while not self.finished():
            time.sleep(self._timeout)
            self._update_status()

        if self.operation_status not in SUCCEEDED:
            from knack.util import CLIError
            raise CLIError("The build with ID '{}' finished with unsuccessful status '{}'. "
                           "Show build details by 'az acr build-task show-build -r {} --build-id {}'. "
                           "Show build logs by 'az acr build-task logs -r {} --build-id {}'.".format(
                               self._build_id,
                               self.operation_status,
                               self._registry_name,
                               self._build_id,
                               self._registry_name,
                               self._build_id
                           ))

    def status(self):
        return self.operation_status

    def finished(self):
        return self.operation_status in FINISHED

    def resource(self):
        return self.operation_result

    def _set_operation_status(self, response):
        if response.status_code == 200:
            self.operation_result = self._deserialize(response)
            self.operation_status = self.operation_result.status or models.BuildStatus.queued.value
            return
        raise CloudError(response)

    def _update_status(self):
        self._response = self._client.send(self._client.get(self._url), stream=False)
        self._set_operation_status(self._response)
