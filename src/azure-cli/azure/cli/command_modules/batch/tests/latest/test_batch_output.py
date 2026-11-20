# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import os
import unittest
from unittest import mock
from urllib.parse import urlsplit

import requests
from urllib3 import HTTPResponse
from azure.core.pipeline import PipelineContext, PipelineResponse
from azure.core.rest._requests_basic import RestRequestsTransportResponse

from azure.cli.core.mock import DummyCli
from azure.cli.core.util import rmtree_with_retry

# Service responses with only the fields the tests check
POOL = {
    'resizeTimeout': 'PT15M',
    'resizeErrors': [{'code': 'AllocationFailed', 'message': 'Quota reached',
                      'values': [{'name': 'Reason', 'value': 'Quota'}]}],
    'virtualMachineConfiguration': {'nodeAgentSKUId': 'batch.node.ubuntu 20.04', 'osDisk': {'diskSizeGB': 100}},
    'stats': {'resourceStats': {'diskReadIOps': 3000000000, 'diskWriteIOps': 2222}},
    'targetNodeCommunicationMode': 'default',
    'currentNodeCommunicationMode': 'simplified',
    'resourceTags': {'tag': 'value'}}
NODE = {
    'endpointConfiguration': {'inboundEndpoints': [{
        'name': 'ssh.0', 'protocol': 'tcp', 'publicIPAddress': '1.2.3.4',
        'publicFQDN': 'node1.eastus2.cloudapp.azure.com', 'frontendPort': 50000, 'backendPort': 22}]}}
JOB = {
    'constraints': {'maxWallClockTime': 'P1279DT12H30M5S'},
    'stats': {'readIOps': 3000000000, 'writeIOps': 5678, 'numSucceededTasks': 7, 'numFailedTasks': 1,
              'numTaskRetries': 2}}
TASK = {
    'constraints': {'maxWallClockTime': 'PT1H', 'retentionTime': 'P7D'},
    'stats': {'readIOps': 10, 'writeIOps': 3000000000}}


class TestBatchOutput(unittest.TestCase):
    """Run data-plane commands with the HTTP pipeline mocked, so the SDK's deserialization and the module's output
    code turn a service response into the printed JSON, as they do for customers."""

    def setUp(self):
        # No Batch settings from AZURE_BATCH_* environment variables or the CLI config
        environ = {name: value for name, value in os.environ.items() if not name.startswith('AZURE_BATCH_')}
        environ_patch = mock.patch.dict(os.environ, environ, clear=True)
        environ_patch.start()
        self.addCleanup(environ_patch.stop)
        self.cli = DummyCli(random_config_dir=True)
        self.addCleanup(self.cli.env_patch.stop)
        self.addCleanup(rmtree_with_retry, self.cli.config.config_dir)

    def _invoke(self, command, responses):
        """Run the command and return its JSON output. `responses` maps (method, path) to (status code, body)."""
        def run(request, **kwargs):  # pylint: disable=unused-argument
            status_code, body = responses[(request.method, urlsplit(request.url).path)]
            internal_response = requests.Response()
            internal_response.status_code = status_code
            internal_response.headers['Content-Type'] = 'application/json; odata=minimalmetadata'
            internal_response.raw = HTTPResponse(body=io.BytesIO(json.dumps(body).encode() if body else b''),
                                                 preload_content=False)
            # The response azure-core's requests transport returns, read in full as for a call without streaming
            response = RestRequestsTransportResponse(request=request, internal_response=internal_response)
            response.read()
            return PipelineResponse(request, response, PipelineContext(None))

        args = command.split() + ['--account-name', 'test1', '--account-key', 'ZmFrZV9hY29jdW50X2tleQ==',
                                  '--account-endpoint', 'https://test1.westus.batch.azure.com', '-o', 'json']
        output = io.StringIO()
        with mock.patch('azure.core.pipeline.Pipeline.run', side_effect=run):
            self.assertEqual(self.cli.invoke(args, out_file=output), 0)
        return json.loads(output.getvalue())

    def test_batch_pool_show_output(self):
        pool = self._invoke('batch pool show --pool-id pool1', {('GET', '/pools/pool1'): (200, POOL)})

        self.assertEqual(pool['stats'], {'resourceStats': {'diskReadIops': 3000000000, 'diskWriteIops': 2222}})
        # List items keep the SDK's attribute names
        self.assertEqual(pool['resizeErrors'], [{'code': 'AllocationFailed', 'message': 'Quota reached',
                                                 'valuesProperty': [{'name': 'Reason', 'value': 'Quota'}]}])
        self.assertNotIn('targetNodeCommunicationMode', pool)
        self.assertNotIn('currentNodeCommunicationMode', pool)
        self.assertNotIn('resourceTags', pool)
        self.assertEqual(pool['resizeTimeout'], 'PT15M')
        self.assertEqual(pool['virtualMachineConfiguration'],
                         {'nodeAgentSkuId': 'batch.node.ubuntu 20.04', 'osDisk': {'diskSizeGb': 100}})

    def test_batch_pool_reset_output(self):
        pool = self._invoke('batch pool reset --pool-id pool1 --start-task-command-line hostname', {
            ('POST', '/pools/pool1/updateproperties'): (204, None),
            ('GET', '/pools/pool1'): (200, POOL)})

        # 'pool reset' prints the SDK model without the module's key changes, unlike 'pool show'
        self.assertEqual(pool['stats']['resourceStats']['diskReadIOps'], 3000000000)
        self.assertEqual(pool['stats']['resourceStats']['diskWriteIOps'], 2222)
        self.assertEqual(pool['resizeErrors'], [{'code': 'AllocationFailed', 'message': 'Quota reached',
                                                 'valuesProperty': [{'name': 'Reason', 'value': 'Quota'}]}])
        self.assertEqual(pool['targetNodeCommunicationMode'], 'default')
        self.assertEqual(pool['currentNodeCommunicationMode'], 'simplified')
        self.assertEqual(pool['resourceTags'], {'tag': 'value'})
        self.assertEqual(pool['resizeTimeout'], '0:15:00')
        self.assertEqual(pool['virtualMachineConfiguration']['nodeAgentSkuId'], 'batch.node.ubuntu 20.04')
        self.assertEqual(pool['virtualMachineConfiguration']['osDisk']['diskSizeGB'], 100)

    def test_batch_node_show_output(self):
        node = self._invoke('batch node show --pool-id pool1 --node-id node1',
                            {('GET', '/pools/pool1/nodes/node1'): (200, NODE)})

        self.assertEqual(node['endpointConfiguration']['inboundEndpoints'], [{
            'name': 'ssh.0', 'protocol': 'tcp', 'publicIpAddress': '1.2.3.4',
            'publicFQDN': 'node1.eastus2.cloudapp.azure.com', 'frontendPort': 50000, 'backendPort': 22}])

    def test_batch_node_remote_login_settings_show_output(self):
        settings = self._invoke('batch node remote-login-settings show --pool-id pool1 --node-id node1', {
            ('GET', '/pools/pool1/nodes/node1/remoteloginsettings'): (
                200, {'remoteLoginIPAddress': '1.2.3.4', 'remoteLoginPort': 50000})})

        self.assertEqual(settings, {'remoteLoginIpAddress': '1.2.3.4', 'remoteLoginPort': 50000})

    def test_batch_job_show_output(self):
        job = self._invoke('batch job show --job-id job1', {('GET', '/jobs/job1'): (200, JOB)})

        self.assertEqual(job['stats'], {'readIops': 3000000000, 'writeIops': 5678, 'numSucceededTasks': 7,
                                        'numFailedTasks': 1, 'numTaskRetries': 2})
        self.assertEqual(job['constraints'], {'maxWallClockTime': 'P1279DT12H30M5S'})

    def test_batch_task_show_output(self):
        task = self._invoke('batch task show --job-id job1 --task-id task1',
                            {('GET', '/jobs/job1/tasks/task1'): (200, TASK)})

        self.assertEqual(task['stats'], {'readIops': 10, 'writeIops': 3000000000})
        self.assertEqual(task['constraints'], {'maxWallClockTime': 'PT1H', 'retentionTime': 'P7D'})
