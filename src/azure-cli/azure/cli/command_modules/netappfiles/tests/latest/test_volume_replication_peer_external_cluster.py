# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from functools import partial
from unittest.mock import Mock, patch

from azure.core.pipeline import PipelineContext, PipelineResponse
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.core.rest import HttpRequest, HttpResponse
from azure.cli.core.aaz._client import AAZMgmtClient
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz._poller import AAZLROPoller
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.netappfiles import NetAppFilesCommandsLoader
from azure.cli.command_modules.netappfiles.custom import VolumeReplicationPeerExternalCluster


class VolumeReplicationPeerExternalClusterTest(unittest.TestCase):

    def setUp(self):
        command_name = 'netappfiles volume replication peer-external-cluster'
        loader = NetAppFilesCommandsLoader(cli_ctx=DummyCli())
        self.command = loader.load_command_table(command_name.split())[command_name]
        self.assertIsInstance(self.command, VolumeReplicationPeerExternalCluster)
        self.command_args = {
            'subscription': '00000000-0000-0000-0000-000000000000',
            'resource_group': 'test-rg',
            'account_name': 'test-account',
            'pool_name': 'test-pool',
            'volume_name': 'test-volume',
            'peer_ip_addresses': ['192.0.2.1'],
        }
        self.polling_url = 'https://management.azure.com/operations/test-peering'
        self.response_body = {
            'properties': {
                'clusterPeeringCommand': 'cluster peer create -peer-addrs 192.0.2.1',
                'passphrase': 'dummy-peering-passphrase',
            },
        }
        self.client = Mock()
        self.client.format_url.side_effect = lambda url, **kwargs: url.format(**kwargs)
        # Use production ARM polling; only HTTP responses and transport are mocked.
        self.client.build_lro_polling = partial(AAZMgmtClient.build_lro_polling, self.client)
        self.client.send_request.side_effect = [
            self._session('POST', 202, {}, {'azure-asyncoperation': self.polling_url}),
            self._session('GET', 200, {'status': 'InProgress'}),
            self._session('GET', 200, {'status': 'Succeeded', **self.response_body}),
        ]

    def _session(self, method, status_code, body, headers=None):
        request = HttpRequest(method, self.polling_url, headers={'x-ms-client-request-id': 'test-request'})
        response = Mock(spec=HttpResponse)
        response.request = request
        response.status_code = status_code
        response.headers = headers or {}
        response.content = json.dumps(body).encode('utf-8')
        response.json.return_value = body
        response.text.return_value = json.dumps(body)
        context = PipelineContext(None)
        context[ContentDecodePolicy.CONTEXT_NAME] = body
        return PipelineResponse(request, response, context)

    def test_registered_command_preserves_passphrase_after_completion(self):
        with patch.object(AAZCommandCtx, 'get_http_client', return_value=self.client), \
                patch.object(self.command, '_output', wraps=self.command._output) as output:
            poller = self.command(self.command_args)
            self.assertIsInstance(poller, AAZLROPoller)
            poller.wait()
            self.assertTrue(poller.done())
            # Waiting completes polling, but output is extracted only by result().
            output.assert_not_called()
            result = poller.result()
            output.assert_called_once()

        self.assertEqual(self.client.send_request.call_count, 3)
        for call in self.client.send_request.call_args_list[1:]:
            self.assertEqual(call.args[0].method, 'GET')
            self.assertEqual(call.args[0].url, self.polling_url)
        self.assertIn('passphrase', result['properties'])
        self.assertEqual(result['properties']['passphrase'], self.response_body['properties']['passphrase'])
        self.assertEqual(result['properties'], self.response_body['properties'])

    def test_no_wait_returns_no_credentials_without_polling(self):
        with patch.object(AAZCommandCtx, 'get_http_client', return_value=self.client), \
                patch.object(self.command, '_output', wraps=self.command._output) as output:
            result = self.command({**self.command_args, 'no_wait': True})
            output.assert_not_called()

        self.assertIsNone(result)
        self.client.send_request.assert_called_once()
        self.assertEqual(self.command.ctx.vars.to_serialized_data(), {})