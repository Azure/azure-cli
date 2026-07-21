# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from msrest import Deserializer
from azure.core.exceptions import HttpResponseError
from azure.core.polling import PollingMethod, LROPoller

from ._constants import get_acr_task_models, get_succeeded_agentpool_status, get_finished_agentpool_status


def delete_agentpool_with_polling(cmd,
                                  client,
                                  agent_pool_name,
                                  registry_name,
                                  resource_group_name):
    deserializer = Deserializer(
        {k: v for k, v in get_acr_task_models(cmd).__dict__.items() if isinstance(v, type)})

    def deserialize_agentpool(response):
        return deserializer('AgentPool', response)

    return LROPoller(
        client=client,
        initial_response=client.get(
            resource_group_name, registry_name, agent_pool_name, cls=lambda x, y, z: x),
        deserialization_callback=deserialize_agentpool,
        polling_method=RunPolling(
            cmd=cmd,
            registry_name=registry_name,
            agent_pool_name=agent_pool_name
        ))


class RunPolling(PollingMethod):  # pylint: disable=too-many-instance-attributes

    def __init__(self, cmd, registry_name, agent_pool_name, timeout=30):
        self._cmd = cmd
        self._registry_name = registry_name
        self._agent_pool_name = agent_pool_name
        self._timeout = timeout
        self._client = None
        self._response = None  # Will hold latest received response
        self._url = None  # The URL used to get the run
        self._deserialize = None  # The deserializer for Run
        self.operation_status = ""
        self.operation_result = None

    def initialize(self, client, initial_response, deserialization_callback):
        self._client = client._client  # pylint: disable=protected-access
        self._response = initial_response
        self._url = initial_response.http_request.url
        self._deserialize = deserialization_callback

        self._set_operation_status(initial_response)

    def run(self):
        while not self.finished():
            time.sleep(self._timeout)
            self._update_status()

        if self.operation_status not in get_succeeded_agentpool_status(self._cmd):
            from knack.util import CLIError
            raise CLIError("The agent pool deletion with name '{}' finished with unsuccessful status '{}'. "
                           "Show run details by 'az acr agentpool show -r {} -n {}'. ".format(
                               self._agent_pool_name,
                               self.operation_status,
                               self._registry_name,
                               self._agent_pool_name
                           ))
        self.operation_result = "Agent '{}' was successfully deleted".format(self._agent_pool_name)

    def status(self):
        return self.operation_status

    def finished(self):
        return self.operation_status in get_finished_agentpool_status(self._cmd)

    def resource(self):
        return self.operation_result

    def _set_operation_status(self, response):
        AgentPoolStatus = self._cmd.get_models('ProvisioningState')
        if response.http_response.status_code == 200 or response.http_response.status_code == 404:
            self.operation_result = self._deserialize(response)
            self.operation_status = self.operation_result.provisioning_state or AgentPoolStatus.succeeded.value
            return
        raise HttpResponseError(response)

    def _update_status(self):
        self._response = self._client._pipeline.run(  # pylint: disable=protected-access
            self._client.get(self._url), stream=False)
        self._set_operation_status(self._response)
