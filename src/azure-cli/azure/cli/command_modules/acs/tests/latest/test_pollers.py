# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock

from azure.cli.command_modules.acs._polling import RunCommandLocationPolling
from azure.core.pipeline import PipelineResponse
from azure.core.rest import HttpRequest, HttpResponse


class TestRunCommandPoller(unittest.TestCase):
    def test_get_status(self):
        poller = RunCommandLocationPolling()

        mock_response = Mock(spec=HttpResponse)
        mock_response.text.return_value = "{\"properties\": {\"provisioningState\": \"Scaling Up\"}}"

        pipeline_response: PipelineResponse[HttpRequest, HttpResponse] = PipelineResponse(Mock(spec=HttpRequest), mock_response, Mock())

        status = poller.get_status(pipeline_response)
        assert status == "Scaling Up"

    def test_get_status_no_provisioning_state(self):
        poller = RunCommandLocationPolling()

        mock_response = Mock(spec=HttpResponse)
        mock_response.text.return_value = "{\"properties\": {\"status\": \"Scaling Up\"}}"

        pipeline_response: PipelineResponse[HttpRequest, HttpResponse] = PipelineResponse(Mock(spec=HttpRequest), mock_response, Mock())

        status = poller.get_status(pipeline_response)
        assert status == "Unknown"
