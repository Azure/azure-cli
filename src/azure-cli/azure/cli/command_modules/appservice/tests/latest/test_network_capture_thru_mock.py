# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest import mock

import websocket

from azure.cli.core.azclierror import AzureResponseError, ValidationError

from azure.cli.command_modules.appservice.network_capture import (
    _download_artifact,
    _run_capture_command,
    _validate_capture_options,
    collect_network_capture,
)

_MODULE = 'azure.cli.command_modules.appservice.network_capture'


class NetworkCaptureValidationTest(unittest.TestCase):

    def test_rejects_values_outside_kudu_limits(self):
        invalid_options = [
            (0, None, 'both', '.'),
            (301, None, 'both', '.'),
            (None, 63, 'both', '.'),
            (None, 65536, 'both', '.'),
            (None, None, 'invalid', '.'),
            (None, None, 'both', '  '),
        ]
        for options in invalid_options:
            with self.subTest(options=options), self.assertRaises(ValidationError):
                _validate_capture_options(*options)

    def test_accepts_complete_packet_snap_length(self):
        _validate_capture_options(300, 0, 'both', '.')


class CollectNetworkCaptureTest(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.session = mock.MagicMock()
        self.session.cookies.get_dict.return_value = {'ARRAffinity': 'worker1'}

        patchers = [
            mock.patch(_MODULE + '._generic_site_operation', return_value=mock.Mock()),
            mock.patch(_MODULE + '.is_linux_webapp', return_value=True),
            mock.patch(_MODULE + '._resolve_single_instance', return_value='worker1'),
            mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net'),
            mock.patch(_MODULE + '.get_scm_site_headers', return_value={'Authorization': 'Bearer token'}),
            mock.patch(_MODULE + '._create_http_session', return_value=self.session),
            mock.patch(_MODULE + '._run_capture_command', return_value=False),
            mock.patch(_MODULE + '._download_artifact'),
        ]
        self.mocks = [patcher.start() for patcher in patchers]
        for patcher in patchers:
            self.addCleanup(patcher.stop)

    @mock.patch(_MODULE + '._request_json')
    def test_collects_analyzes_and_downloads_both_artifacts(self, request_json):
        request_json.side_effect = [
            {'autoAnalysisEnabled': True},
            {'sessionId': 'capture-1', 'captureCommand': 'server generated command'},
            {'sessionId': 'capture-1', 'status': 'Ready', 'truncated': True},
        ]

        with tempfile.TemporaryDirectory() as destination:
            result = collect_network_capture(
                self.cmd, 'rg', 'app', instance='worker1', duration=60, interface='eth0',
                snap_length=128, capture_filter='port 443', destination=destination)

        create_call = request_json.call_args_list[1]
        self.assertEqual(create_call.args[:3],
                         (self.session, 'POST',
                          'https://app.scm.azurewebsites.net/api/networkcapture/captures'))
        self.assertEqual(create_call.kwargs['json'], {
            'iface': 'eth0',
            'duration': 60,
            'snaplen': 128,
            'filter': 'port 443',
        })
        self.assertEqual(result['status'], 'Ready')
        self.assertTrue(result['truncated'])
        self.assertTrue(result['packetCapture'].endswith('app_capture-1.pcap'))
        self.assertTrue(result['report'].endswith('app_capture-1.pcap.html'))
        self.assertEqual(self.mocks[-1].call_count, 2)

    @mock.patch(_MODULE + '._request_json')
    def test_auto_analysis_disabled_downloads_only_pcap(self, request_json):
        request_json.side_effect = [
            {'autoAnalysisEnabled': False},
            {'sessionId': 'capture-1', 'captureCommand': 'server generated command'},
            {'sessionId': 'capture-1', 'status': 'Captured'},
        ]

        with tempfile.TemporaryDirectory() as destination:
            result = collect_network_capture(self.cmd, 'rg', 'app', destination=destination)

        self.assertEqual(result['status'], 'Captured')
        self.assertIsNone(result['report'])
        self.assertEqual(self.mocks[-1].call_count, 1)

    @mock.patch(_MODULE + '._request_json')
    def test_report_only_surfaces_analysis_failure(self, request_json):
        request_json.side_effect = [
            {'autoAnalysisEnabled': True},
            {'sessionId': 'capture-1', 'captureCommand': 'server generated command'},
            {'sessionId': 'capture-1', 'status': 'Failed', 'error': 'invalid pcap'},
        ]

        with tempfile.TemporaryDirectory() as destination:
            with self.assertRaisesRegex(AzureResponseError, 'invalid pcap'):
                collect_network_capture(
                    self.cmd, 'rg', 'app', artifact='report', destination=destination)


class CaptureShellTest(unittest.TestCase):

    @mock.patch('websocket.create_connection')
    def test_connection_close_after_submission_is_not_a_capture_failure(self, create_connection):
        connection = create_connection.return_value
        connection.recv.side_effect = websocket.WebSocketConnectionClosedException()

        interrupted = _run_capture_command(
            'https://app.scm.azurewebsites.net', {'Authorization': 'Bearer token'},
            {'ARRAffinity': 'worker1'}, 'server generated command', 30)

        self.assertFalse(interrupted)
        connection.send_binary.assert_called_once_with(b'server generated command\nexit\n')
        self.assertIn('ARRAffinity=worker1', create_connection.call_args.kwargs['cookie'])
        connection.close.assert_called_once()


class ArtifactDownloadTest(unittest.TestCase):

    def test_download_is_atomic_and_does_not_overwrite(self):
        response = mock.MagicMock(status_code=200)
        response.iter_content.return_value = [b'pcap', b'-data']
        session = mock.MagicMock()
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as destination:
            artifact_path = os.path.join(destination, 'capture.pcap')
            _download_artifact(session, 'https://app/capture/download', artifact_path)
            with open(artifact_path, 'rb') as artifact_file:
                self.assertEqual(artifact_file.read(), b'pcap-data')
            self.assertEqual(os.listdir(destination), ['capture.pcap'])

            with self.assertRaisesRegex(ValidationError, 'already exists'):
                _download_artifact(session, 'https://app/capture/download', artifact_path)


if __name__ == '__main__':
    unittest.main()