# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import websocket
from knack.prompting import NoTTYException

from azure.cli.core.azclierror import AzureResponseError, ValidationError

from azure.cli.command_modules.appservice.network_capture import (
    _run_capture_command,
    _select_target_instance,
    _validate_capture_options,
    collect_network_capture,
)

_MODULE = 'azure.cli.command_modules.appservice.network_capture'


class NetworkCaptureValidationTest(unittest.TestCase):

    def test_rejects_values_outside_kudu_limits(self):
        for duration in (0, 301):
            with self.subTest(duration=duration), self.assertRaises(ValidationError):
                _validate_capture_options(duration)

    def test_accepts_maximum_duration(self):
        _validate_capture_options(300)


class NetworkCaptureInstanceSelectionTest(unittest.TestCase):

    @mock.patch(_MODULE + '.prompt_choice_list')
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=['worker2'])
    def test_explicit_instance_bypasses_prompt(self, resolve_instances, prompt):
        selected = _select_target_instance(mock.Mock(), 'rg', 'app', 'worker2', None)

        self.assertEqual(selected, 'worker2')
        resolve_instances.assert_called_once_with(mock.ANY, 'rg', 'app', 'worker2', None)
        prompt.assert_not_called()

    @mock.patch(_MODULE + '.prompt_choice_list', return_value=1)
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=['worker1', 'worker2'])
    def test_omitted_instance_prompts_with_current_workers(self, resolve_instances, prompt):
        selected = _select_target_instance(mock.Mock(), 'rg', 'app', None, 'staging')

        self.assertEqual(selected, 'worker2')
        resolve_instances.assert_called_once_with(mock.ANY, 'rg', 'app', 'all', 'staging')
        prompt.assert_called_once_with(
            '\nSelect the instance where you will reproduce the issue:', ['worker1', 'worker2'])

    @mock.patch(_MODULE + '.prompt_choice_list', side_effect=NoTTYException)
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=['worker1'])
    def test_omitted_instance_requires_flag_without_tty(self, _resolve_instances, _prompt):
        with self.assertRaisesRegex(ValidationError, 'Specify --instance'):
            _select_target_instance(mock.Mock(), 'rg', 'app', None, None)

    def test_rejects_all_instances(self):
        with self.assertRaisesRegex(ValidationError, 'one web app instance'):
            _select_target_instance(mock.Mock(), 'rg', 'app', 'all', None)


class CollectNetworkCaptureTest(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.session = mock.MagicMock()
        self.session.cookies.get_dict.return_value = {'ARRAffinity': 'worker1'}

        patchers = [
            mock.patch(_MODULE + '._generic_site_operation', return_value=mock.Mock()),
            mock.patch(_MODULE + '.is_linux_webapp', return_value=True),
            mock.patch(_MODULE + '._select_target_instance', return_value='worker1'),
            mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net'),
            mock.patch(_MODULE + '.get_scm_site_headers', return_value={'Authorization': 'Bearer token'}),
            mock.patch(_MODULE + '._create_http_session', return_value=self.session),
            mock.patch(_MODULE + '._run_capture_command', return_value=False),
        ]
        self.mocks = [patcher.start() for patcher in patchers]
        for patcher in patchers:
            self.addCleanup(patcher.stop)

    @mock.patch(_MODULE + '.logger.warning')
    @mock.patch(_MODULE + '._request_json')
    def test_collects_analyzes_and_returns_kudu_links(self, request_json, warning):
        request_json.side_effect = [
            {'id': 'capture-1', 'captureCommand': 'server generated command'},
            {
                'id': 'capture-1',
                'status': 'Ready',
                'truncated': True,
                'downloadUrl': '/api/networkcapture/captures/capture-1/download',
                'reportUrl': '/api/networkcapture/captures/capture-1/report',
            },
        ]

        output = StringIO()
        with redirect_stdout(output):
            result = collect_network_capture(self.cmd, 'rg', 'app', instance='worker1')

        create_call = request_json.call_args_list[0]
        self.assertEqual(create_call.args[:3],
                         (self.session, 'POST',
                          'https://app.scm.azurewebsites.net/api/networkcapture/captures'))
        self.assertEqual(create_call.kwargs['json'], {'durationSeconds': 60})
        request_json.assert_any_call(
            self.session, 'POST',
            'https://app.scm.azurewebsites.net/api/networkcapture/captures/capture-1/analyze')
        self.assertIsNone(result)
        rendered = output.getvalue()
        self.assertIn('Capture ID: capture-1', rendered)
        self.assertIn('https://app.scm.azurewebsites.net/api/networkcapture/captures/capture-1/download?instance=worker1',
                  rendered)
        self.assertIn('https://app.scm.azurewebsites.net/api/networkcapture/captures/capture-1/report?instance=worker1',
                  rendered)
        self.assertIn('Microsoft Network Monitor or Wireshark', rendered)
        self.assertIn('Capture ID: capture-1\n\nDownload raw packet capture:', rendered)
        self.assertIn('download?instance=worker1\n\nView analysis report:', rendered)
        advisory = next(call.args for call in warning.call_args_list
                if call.args and call.args[0].startswith('What you should know'))
        self.assertIn('help troubleshoot TCP packet loss', advisory[0])
        self.assertIn('selected instance serving your app', advisory[0])
        self.assertIn('Capture duration is 60 seconds by default', advisory[0])
        self.assertIn('capture up to 100 MB of data', advisory[0])
        self.assertIn('https://www.wireshark.org/', advisory[0])
        self.assertEqual(len(advisory), 1)
        self.assertIn(mock.call(''), warning.call_args_list)
        progress_calls = [call.args for call in warning.call_args_list
                          if call.args and call.args[0].startswith('[%d/%d]')]
        self.assertEqual(progress_calls, [
            ('[%d/%d] Preparing network capture...', 1, 4),
            ("[%d/%d] Capturing network traffic on web app '%s'...", 2, 4, 'app'),
            ('[%d/%d] Packet collection finished. Analyzing capture...', 3, 4),
            ('[%d/%d] Network capture collected successfully.', 4, 4),
        ])

    @mock.patch(_MODULE + '._request_json')
    def test_collect_only_omits_report_link(self, request_json):
        request_json.side_effect = [
            {'id': 'capture-1', 'captureCommand': 'server generated command'},
            {
                'id': 'capture-1',
                'status': 'Ready',
                'downloadUrl': '/api/networkcapture/captures/capture-1/download',
                'reportUrl': '/api/networkcapture/captures/capture-1/report',
            },
        ]

        output = StringIO()
        with redirect_stdout(output):
            result = collect_network_capture(self.cmd, 'rg', 'app', collect_only=True)

        self.assertIsNone(result)
        request_json.assert_any_call(
            self.session, 'POST',
            'https://app.scm.azurewebsites.net/api/networkcapture/captures/capture-1/analyze')
        rendered = output.getvalue()
        self.assertIn('/capture-1/download', rendered)
        self.assertNotIn('/capture-1/report', rendered)
        self.assertIn('Microsoft Network Monitor or Wireshark', rendered)

    @mock.patch(_MODULE + '._request_json')
    def test_surfaces_analysis_failure(self, request_json):
        request_json.side_effect = [
            {'id': 'capture-1', 'captureCommand': 'server generated command'},
            {'id': 'capture-1', 'status': 'Failed', 'error': 'invalid pcap'},
        ]

        with self.assertRaisesRegex(AzureResponseError, 'invalid pcap'):
            collect_network_capture(self.cmd, 'rg', 'app')

    @mock.patch(_MODULE + '._request_json')
    def test_no_packets_omits_report_link(self, request_json):
        request_json.side_effect = [
            {'id': 'capture-1', 'captureCommand': 'server generated command'},
            {'id': 'capture-1', 'status': 'NoPackets'},
        ]

        output = StringIO()
        with redirect_stdout(output):
            result = collect_network_capture(self.cmd, 'rg', 'app')

        self.assertIsNone(result)
        rendered = output.getvalue()
        self.assertIn('No packets were captured during the capture window', rendered)
        self.assertIn('app running on instance (worker)', rendered)
        self.assertIn('was not receiving traffic or making any outbound calls', rendered)
        self.assertIn('Please generate a repro and capture again.', rendered)
        self.assertNotIn('instance (worker1)', rendered)
        self.assertNotIn('Capture ID:', rendered)
        self.assertNotIn('/capture-1/report', rendered)
        self.assertNotIn('For deeper investigation', rendered)
        self.assertNotIn('Kudu access is required', rendered)


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


if __name__ == '__main__':
    unittest.main()