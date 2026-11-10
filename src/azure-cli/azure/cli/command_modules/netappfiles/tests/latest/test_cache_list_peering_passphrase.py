# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch

from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.netappfiles import NetAppFilesCommandsLoader
from azure.cli.command_modules.netappfiles.custom import CacheListPeeringPassphrase


class CacheListPeeringPassphraseTest(unittest.TestCase):

    def test_registered_command_preserves_cluster_peering_passphrase(self):
        command_name = 'netappfiles cache list-peering-passphrase'
        loader = NetAppFilesCommandsLoader(cli_ctx=DummyCli())
        command_table = loader.load_command_table(command_name.split())
        command = command_table[command_name]
        self.assertIsInstance(command, CacheListPeeringPassphrase)

        response_body = {
            'clusterPeeringCommand': 'cluster peer create -peer-addrs 192.0.2.1',
            'clusterPeeringPassphrase': 'dummy-peering-passphrase',
            'vserverPeeringCommand': 'vserver peer accept -vserver cache-vserver',
        }
        session = Mock()
        session.http_response.status_code = 200
        session.context = {ContentDecodePolicy.CONTEXT_NAME: response_body}
        client = Mock()
        client.send_request.return_value = session

        # Mock only the HTTP client; retain command execution, response schema,
        # and output serialization so secret filtering regressions are caught.
        with patch.object(AAZCommandCtx, 'get_http_client', return_value=client):
            result = command({
                'subscription': '00000000-0000-0000-0000-000000000000',
                'resource_group': 'test-rg',
                'account_name': 'test-account',
                'pool_name': 'test-pool',
                'cache_name': 'test-cache',
            })

        client.send_request.assert_called_once()
        self.assertIn('clusterPeeringPassphrase', result)
        self.assertEqual(result['clusterPeeringPassphrase'], response_body['clusterPeeringPassphrase'])
        self.assertEqual(result, response_body)