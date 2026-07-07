# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import io
import unittest
from unittest import mock

import requests
import websocket

from azure.cli.core.azclierror import (
    ResourceNotFoundError,
    ValidationError,
    AzureConnectionError,
    CLIInternalError,
)
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.appservice.webapp_exec import (
    webapp_exec,
    _resolve_target_instances,
    _execute_command_on_instance,
    _parse_server_message,
    _friendly_exec_error_message,
    _read_from_server,
    _start_shell_session,
)

_MODULE = 'azure.cli.command_modules.appservice.webapp_exec'


def _get_test_cmd():
    """Return a mock CLI context (`cmd`) to pass as the first argument of `webapp_exec`."""
    from azure.cli.core.mock import DummyCli
    from azure.cli.core import AzCommandsLoader
    from azure.cli.core.commands import AzCliCommand
    cli_ctx = DummyCli()
    loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_APPSERVICE)
    cmd = AzCliCommand(loader, 'test', None)
    cmd.command_kwargs = {'resource_type': ResourceType.MGMT_APPSERVICE}
    cmd.cli_ctx = cli_ctx
    return cmd


def _instance(name):
    """Return a mock instance object as `list_instances` yields."""
    inst = mock.Mock()
    inst.name = name
    return inst


class WebappExecValidationTest(unittest.TestCase):
    """Validate the parameter-checking branches of webapp_exec."""

    def setUp(self):
        # Set up default mocks so webapp_exec sees an existing Linux site
        site_op_patcher = mock.patch(_MODULE + '._generic_site_operation', return_value=mock.Mock())
        is_linux_patcher = mock.patch(_MODULE + '.is_linux_webapp', return_value=True)
        self.site_op = site_op_patcher.start()
        self.is_linux = is_linux_patcher.start()
        self.addCleanup(site_op_patcher.stop)
        self.addCleanup(is_linux_patcher.stop)
        self.cmd = _get_test_cmd()

    def test_site_not_found_raises(self):
        self.site_op.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, "Unable to find web app"):
            webapp_exec(self.cmd, 'rg', 'app')

    def test_non_linux_site_raises(self):
        self.is_linux.return_value = False
        with self.assertRaisesRegex(ValidationError, "not a Linux web app"):
            webapp_exec(self.cmd, 'rg', 'app')

    def test_execute_mode_requires_command(self):
        with self.assertRaisesRegex(ValidationError, "Command is required"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute')

    def test_execute_mode_rejects_shell(self):
        with self.assertRaisesRegex(ValidationError, r"--shell is only supported in 'shell' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls', shell='/bin/sh')

    def test_shell_mode_rejects_command(self):
        with self.assertRaisesRegex(ValidationError, r"--command is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', exec_command='ls')

    def test_shell_mode_rejects_args(self):
        with self.assertRaisesRegex(ValidationError, r"--args is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', args=['-l'])

    def test_shell_mode_rejects_working_directory(self):
        with self.assertRaisesRegex(ValidationError, r"--working-directory is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', working_directory='/home')

    def test_shell_mode_rejects_all_instances(self):
        with self.assertRaisesRegex(ValidationError, "single instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', instance='all')

    def test_shell_mode_rejects_instance_list(self):
        with self.assertRaisesRegex(ValidationError, "single instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', instance='i1,i2')

    def test_shell_mode_rejects_relative_shell_path(self):
        with self.assertRaisesRegex(ValidationError, "absolute path"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', shell='bash')

    def test_shell_mode_rejects_overlong_shell_path(self):
        with self.assertRaisesRegex(ValidationError, "too long"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', shell='/' + 'a' * 300)

    def test_invalid_mode_raises(self):
        with self.assertRaisesRegex(ValidationError, "Invalid mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='bogus')

    @mock.patch(_MODULE + '._start_shell_session')
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_shell_mode_happy_path_starts_session(self, _scm, _headers, _resolve, start_session):
        result = webapp_exec(self.cmd, 'rg', 'app', mode='shell')
        self.assertIsNone(result)
        start_session.assert_called_once()

    @mock.patch(_MODULE + '._execute_in_parallel', return_value=[{'status': 'success'}])
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_execute_mode_happy_path_runs_in_parallel(self, _scm, _headers, _resolve, run_parallel):
        result = webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls')
        self.assertEqual(result, [{'status': 'success'}])
        run_parallel.assert_called_once()


class ResolveTargetInstancesTest(unittest.TestCase):
    """Validate _resolve_target_instances instance-selection logic."""

    def setUp(self):
        self.cmd = _get_test_cmd()

    @mock.patch(_MODULE + '.list_instances')
    def test_none_returns_single_default(self, list_mock):
        # No instance requested -> a single unpinned target; no list_instances call needed.
        self.assertEqual(_resolve_target_instances(self.cmd, 'rg', 'app', None, None), [None])
        list_mock.assert_not_called()

    @mock.patch(_MODULE + '.list_instances', return_value=[_instance('b'), _instance('a')])
    def test_all_returns_sorted_names(self, _list_mock):
        self.assertEqual(_resolve_target_instances(self.cmd, 'rg', 'app', 'all', None), ['a', 'b'])

    @mock.patch(_MODULE + '.list_instances', return_value=[])
    def test_all_with_no_instances_raises(self, _list_mock):
        with self.assertRaisesRegex(ValidationError, "No instances found"):
            _resolve_target_instances(self.cmd, 'rg', 'app', 'all', None)

    @mock.patch(_MODULE + '.list_instances', return_value=[_instance('i1'), _instance('i2')])
    def test_valid_comma_list_returns_requested(self, _list_mock):
        self.assertEqual(_resolve_target_instances(self.cmd, 'rg', 'app', 'i1, i2', None), ['i1', 'i2'])

    @mock.patch(_MODULE + '.list_instances', return_value=[_instance('i1')])
    def test_invalid_instance_raises(self, _list_mock):
        with self.assertRaisesRegex(ValidationError, "not valid for this web app"):
            _resolve_target_instances(self.cmd, 'rg', 'app', 'i1,nope', None)


class ParseServerMessageTest(unittest.TestCase):
    """Validate _parse_server_message body handling."""

    def test_none_body_returns_none(self):
        self.assertIsNone(_parse_server_message(None))

    def test_empty_and_whitespace_body_returns_none(self):
        self.assertIsNone(_parse_server_message(''))
        self.assertIsNone(_parse_server_message('   \n'))

    def test_json_message_field_is_extracted(self):
        self.assertEqual(_parse_server_message('{"Message": "hello"}'), 'hello')

    def test_json_dict_without_message_returns_none(self):
        self.assertIsNone(_parse_server_message('{"Other": "x"}'))

    def test_non_json_text_returned_verbatim(self):
        self.assertEqual(_parse_server_message('non json text'), 'non json text')

    def test_json_non_dict_returned_as_text(self):
        self.assertEqual(_parse_server_message('[1, 2]'), '[1, 2]')

    def test_bytes_body_is_decoded(self):
        self.assertEqual(_parse_server_message(b'{"Message": "hi"}'), 'hi')


class FriendlyExecErrorMessageTest(unittest.TestCase):
    """Validate _friendly_exec_error_message fallback behavior."""

    def test_empty_body_uses_fallback(self):
        self.assertEqual(
            _friendly_exec_error_message(''),
            "The request could not be completed. Please try again later.")

    def test_message_passthrough(self):
        self.assertEqual(_friendly_exec_error_message('{"Message": "denied"}'), 'denied')


class ExecuteCommandOnInstanceTest(unittest.TestCase):
    """Validate _execute_command_on_instance request building and response handling."""

    @mock.patch('requests.post', autospec=True)
    def test_success_returns_parsed_message(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=202, text='{"Message": "done"}')
        result = _execute_command_on_instance('https://scm', {}, {}, 'ls')
        self.assertEqual(result, 'done')

    @mock.patch('requests.post', autospec=True)
    def test_body_omits_optional_fields_when_absent(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=202, text='')
        _execute_command_on_instance('https://scm', {}, {}, 'ls')
        self.assertEqual(post_mock.call_args.kwargs['json'], {'Command': 'ls'})

    @mock.patch('requests.post', autospec=True)
    def test_body_includes_args_and_working_directory(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=202, text='')
        _execute_command_on_instance('https://scm', {}, {}, 'bash', args=['-c', 'pwd'], working_directory='/home')
        self.assertEqual(
            post_mock.call_args.kwargs['json'],
            {'Command': 'bash', 'Args': ['-c', 'pwd'], 'WorkingDirectory': '/home'})

    @mock.patch('requests.post', autospec=True)
    def test_non_202_raises_internal_error_with_message(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=500, text='{"Message": "Internal Error"}')
        with self.assertRaisesRegex(CLIInternalError, "Internal Error"):
            _execute_command_on_instance('https://scm', {}, {}, 'ls')

    @mock.patch('requests.post', autospec=True)
    def test_non_202_empty_body_uses_fallback_message(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=500, text='')
        with self.assertRaisesRegex(CLIInternalError, "could not be completed"):
            _execute_command_on_instance('https://scm', {}, {}, 'ls')

    @mock.patch('requests.post', autospec=True)
    def test_request_exception_raises_connection_error(self, post_mock):
        post_mock.side_effect = requests.exceptions.ConnectTimeout('timed out')
        with self.assertRaisesRegex(AzureConnectionError, "Could not connect"):
            _execute_command_on_instance('https://scm', {}, {}, 'ls')


class ReadFromServerTest(unittest.TestCase):
    """Validate _read_from_server opcode handling and UTF-8 decoding."""

    @staticmethod
    def _run(frames):
        # Mock WebSocket frames containing shell output from the server. Pass frames through
        # _read_from_server and return the parsed output for testing _read_from_server.
        import threading
        ws = mock.Mock()
        ws.recv_data.side_effect = list(frames)
        closed = threading.Event()
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        # Redirect stdout to an in-memory buffer to capture what _read_from_server prints.
        out = io.StringIO()
        with mock.patch('sys.stdout', out):
            _read_from_server(ws, closed, decoder)
        return out.getvalue(), closed

    def test_text_frame_written_to_stdout(self):
        out, closed = self._run([
            (websocket.ABNF.OPCODE_TEXT, b'hello'),
            (websocket.ABNF.OPCODE_CLOSE, b''),
        ])
        self.assertEqual(out, 'hello')
        self.assertTrue(closed.is_set())

    def test_binary_frame_written_to_stdout(self):
        out, _closed = self._run([
            (websocket.ABNF.OPCODE_BINARY, b'hi'),
            (websocket.ABNF.OPCODE_CLOSE, b''),
        ])
        self.assertEqual(out, 'hi')

    def test_ping_and_pong_frames_are_skipped(self):
        out, _closed = self._run([
            (websocket.ABNF.OPCODE_PING, b'x'),
            (websocket.ABNF.OPCODE_PONG, b'y'),
            (websocket.ABNF.OPCODE_TEXT, b'ok'),
            (websocket.ABNF.OPCODE_CLOSE, b''),
        ])
        self.assertEqual(out, 'ok')

    def test_close_frame_stops_before_writing(self):
        out, closed = self._run([
            (websocket.ABNF.OPCODE_CLOSE, b''),
        ])
        self.assertEqual(out, '')
        self.assertTrue(closed.is_set())

    def test_multibyte_utf8_split_across_frames_is_decoded(self):
        # 'e-acute' is bytes 0xC3 0xA9; deliver the two bytes in separate frames.
        out, _closed = self._run([
            (websocket.ABNF.OPCODE_BINARY, b'\xc3'),
            (websocket.ABNF.OPCODE_BINARY, b'\xa9'),
            (websocket.ABNF.OPCODE_CLOSE, b''),
        ])
        self.assertEqual(out, '\u00e9')


class ShellSessionConnectTest(unittest.TestCase):
    """Validate _start_shell_session URL/cookie building and handshake error mapping."""

    def setUp(self):
        # Stub every post-connect step so only the connection setup runs.
        patchers = [
            mock.patch(_MODULE + '._read_from_server'),
            mock.patch(_MODULE + '._send_terminal_resize'),
            mock.patch(_MODULE + '._send_to_server_windows'),
            mock.patch(_MODULE + '._send_to_server_non_windows'),
            mock.patch(_MODULE + '._enable_windows_vt_output', return_value=None),
            mock.patch('websocket.create_connection'),
        ]
        started = [p.start() for p in patchers]
        for patcher in patchers:
            self.addCleanup(patcher.stop)
        # Save a reference to the create_connection mock so each test can
        # check the parameters used when called (URL, headers, and cookie)
        self.create_conn = started[-1]

    def test_builds_wss_url_and_forwards_headers(self):
        headers = {'Authorization': 'Bearer token'}
        _start_shell_session('https://scm.example', headers)
        self.assertEqual(self.create_conn.call_args.args[0], 'wss://scm.example/exec/shell')
        self.assertEqual(self.create_conn.call_args.kwargs['header'], headers)

    def test_shell_param_is_appended_and_url_encoded(self):
        _start_shell_session('https://scm.example', {}, shell='/bin/bash')
        self.assertEqual(
            self.create_conn.call_args.args[0],
            'wss://scm.example/exec/shell?shell=%2Fbin%2Fbash')

    def test_cookies_are_formatted_into_cookie_string(self):
        _start_shell_session('https://scm.example', {}, cookies={'ARRAffinity': 'abc'})
        self.assertEqual(self.create_conn.call_args.kwargs['cookie'], 'ARRAffinity=abc')

    def test_no_cookies_sends_none(self):
        _start_shell_session('https://scm.example', {})
        self.assertIsNone(self.create_conn.call_args.kwargs['cookie'])

    def test_bad_handshake_raises_internal_error(self):
        self.create_conn.side_effect = websocket.WebSocketBadStatusException(
            'Handshake status 403', 403, resp_body='{"Message": "Access denied"}')
        with self.assertRaisesRegex(CLIInternalError, 'Access denied'):
            _start_shell_session('https://scm.example', {})

    def test_connection_failure_raises_connection_error(self):
        self.create_conn.side_effect = OSError('refused')
        with self.assertRaisesRegex(AzureConnectionError, 'Could not connect'):
            _start_shell_session('https://scm.example', {})


if __name__ == '__main__':
    unittest.main()
