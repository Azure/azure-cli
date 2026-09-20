# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import io
import ssl
import unittest
from unittest import mock

import requests
import websocket

from azure.cli.core.azclierror import (
    ResourceNotFoundError,
    ValidationError,
    AzureConnectionError,
    AzureResponseError,
    CLIInternalError,
)
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.appservice.webapp_exec import (
    webapp_exec,
    _resolve_target_instances,
    _build_execute_invocation,
    _run_execute_on_instance,
    _execute_command_on_instance,
    _parse_server_message,
    _friendly_exec_error_message,
    _read_from_server,
    _send_to_server_windows,
    _send_to_server_non_windows,
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
        with self.assertRaisesRegex(ValidationError, "Either --command or --shell-command is required"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute')

    def test_execute_mode_rejects_blank_shell_command(self):
        with self.assertRaisesRegex(ValidationError, "--shell-command must not be empty"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', shell_command='   ')

    def test_execute_mode_rejects_command_and_shell_command_together(self):
        with self.assertRaisesRegex(ValidationError, "either --command or --shell-command, not both"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls', shell_command='ls')

    def test_execute_mode_rejects_shell_without_shell_command(self):
        with self.assertRaisesRegex(ValidationError, "--shell is only valid together with --shell-command"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls', shell='/bin/sh')

    def test_execute_mode_rejects_invalid_working_directory(self):
        for working_directory in ('   ', 'home/site'):
            with self.subTest(working_directory=working_directory):
                with self.assertRaisesRegex(ValidationError, "--working-directory must be a non-empty absolute path"):
                    webapp_exec(
                        self.cmd, 'rg', 'app', mode='execute', exec_command='ls',
                        working_directory=working_directory)

    def test_shell_mode_rejects_command(self):
        with self.assertRaisesRegex(ValidationError, r"--command is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', exec_command='ls')

    def test_shell_mode_rejects_shell_command(self):
        with self.assertRaisesRegex(ValidationError, r"--shell-command is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', shell_command='ls')

    def test_shell_mode_rejects_working_directory(self):
        with self.assertRaisesRegex(ValidationError, r"--working-directory is only supported in 'execute' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', working_directory='/home')

    def test_shell_mode_rejects_all_instances(self):
        with self.assertRaisesRegex(ValidationError, "single instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', instance='all')

    def test_shell_mode_rejects_all_instances_with_whitespace(self):
        with self.assertRaisesRegex(ValidationError, "single instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', instance=' all ')

    def test_shell_mode_rejects_instance_list(self):
        with self.assertRaisesRegex(ValidationError, "single instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', instance='i1,i2')

    def test_shell_mode_rejects_relative_shell_path(self):
        with self.assertRaisesRegex(ValidationError, "absolute path"):
            webapp_exec(self.cmd, 'rg', 'app', mode='shell', shell='bash')

    def test_invalid_mode_raises(self):
        with self.assertRaisesRegex(ValidationError, "Invalid mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='bogus')

    def test_invalid_target_raises(self):
        with self.assertRaisesRegex(ValidationError, "Invalid target"):
            webapp_exec(self.cmd, 'rg', 'app', target='sidecar')

    @mock.patch(_MODULE + '._get_scm_url')
    def test_execute_mode_rejects_kudu_target_before_scm_connection(self, scm_mock):
        with self.assertRaisesRegex(ValidationError, "supported only in 'shell' mode"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls', target='kudu')
        scm_mock.assert_not_called()

    @mock.patch(_MODULE + '._start_shell_session')
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_shell_mode_happy_path_starts_session(self, _scm, _headers, _resolve, start_session):
        result = webapp_exec(self.cmd, 'rg', 'app', mode='shell', target='kudu')
        self.assertIsNone(result)
        start_session.assert_called_once_with(
            'https://app.scm.azurewebsites.net', {}, {}, shell=None, target='kudu')

    @mock.patch(_MODULE + '._execute_in_parallel', return_value=[{'status': 'accepted'}])
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_execute_mode_happy_path_runs_in_parallel(self, _scm, _headers, _resolve, run_parallel):
        result = webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls')
        self.assertEqual(result, [{'status': 'accepted'}])
        run_parallel.assert_called_once()

    @mock.patch(_MODULE + '._execute_in_parallel', return_value=[{'status': 'accepted'}])
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_execute_mode_shell_command_happy_path(self, _scm, _headers, _resolve, run_parallel):
        result = webapp_exec(self.cmd, 'rg', 'app', mode='execute',
                             shell_command='echo hi > /home/LogFiles/out.txt')
        self.assertEqual(result, [{'status': 'accepted'}])
        run_parallel.assert_called_once()

    @mock.patch(_MODULE + '._execute_in_parallel',
                return_value=[{'instance': 'default', 'status': 'failed', 'error': 'boom'}])
    @mock.patch(_MODULE + '._resolve_target_instances', return_value=[None])
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    def test_execute_mode_failed_instance_raises(self, _scm, _headers, _resolve, _run_parallel):
        with self.assertRaisesRegex(AzureResponseError, "not accepted on 1 of 1 instance"):
            webapp_exec(self.cmd, 'rg', 'app', mode='execute', exec_command='ls')


class BuildExecuteInvocationTest(unittest.TestCase):
    """Validate how --command / --shell-command map to the backend (command, args) argv pair."""

    def test_command_is_split_into_executable_and_args(self):
        command, args = _build_execute_invocation('python /home/app.py --port 8080', None, None)
        self.assertEqual(command, 'python')
        self.assertEqual(args, ['/home/app.py', '--port', '8080'])

    def test_command_respects_quoting(self):
        command, args = _build_execute_invocation('touch "my file.txt"', None, None)
        self.assertEqual(command, 'touch')
        self.assertEqual(args, ['my file.txt'])

    def test_shell_command_wraps_in_default_shell(self):
        command, args = _build_execute_invocation(None, 'echo hi | grep h', None)
        self.assertEqual(command, '/bin/bash')
        self.assertEqual(args, ['-c', 'echo hi | grep h'])

    def test_shell_command_honors_custom_shell(self):
        command, args = _build_execute_invocation(None, 'echo hi', '/bin/sh')
        self.assertEqual(command, '/bin/sh')
        self.assertEqual(args, ['-c', 'echo hi'])

    @mock.patch(_MODULE + '.logger.warning')
    def test_shell_command_contents_are_not_logged(self, warning_mock):
        _build_execute_invocation(None, 'echo super-secret-value', None)
        warning_mock.assert_called_once_with("Running shell command with %s.", '/bin/bash')

    @mock.patch(_MODULE + '.logger.warning')
    def test_direct_command_contents_are_not_logged(self, warning_mock):
        _build_execute_invocation('curl --header super-secret-value', None, None)
        warning_mock.assert_not_called()

    def test_empty_command_raises(self):
        with self.assertRaisesRegex(ValidationError, "must not be empty"):
            _build_execute_invocation('   ', None, None)

    def test_unbalanced_quotes_raises(self):
        with self.assertRaisesRegex(ValidationError, "Could not parse --command"):
            _build_execute_invocation('echo "unterminated', None, None)

    def test_single_token_command_has_no_args(self):
        command, args = _build_execute_invocation('nginx', None, None)
        self.assertEqual(command, 'nginx')
        self.assertEqual(args, [])

    def test_shell_operators_pass_through_as_literal_args(self):
        command, args = _build_execute_invocation('myprog >&>>&&&&>', None, None)
        self.assertEqual(command, 'myprog')
        self.assertEqual(args, ['>&>>&&&&>'])

    def test_shell_command_empty_shell_falls_back_to_default(self):
        command, args = _build_execute_invocation(None, 'echo hi', '')
        self.assertEqual(command, '/bin/bash')
        self.assertEqual(args, ['-c', 'echo hi'])


class RunExecuteOnInstanceTest(unittest.TestCase):
    """Validate per-instance result messages."""

    @mock.patch(_MODULE + '.logger.warning')
    @mock.patch(_MODULE + '._execute_command_on_instance', return_value='Command accepted.')
    def test_accepted_without_explicit_instance_omits_instance_label(self, _execute_mock, warning_mock):
        result = _run_execute_on_instance(None, 'https://scm', {}, 'ls', [], None)
        warning_mock.assert_called_once_with("%s", "Command accepted.")
        self.assertEqual(result['instance'], 'default')

    @mock.patch(_MODULE + '.logger.warning')
    @mock.patch(_MODULE + '._execute_command_on_instance', side_effect=CLIInternalError('rejected'))
    def test_failed_without_explicit_instance_omits_instance_label(self, _execute_mock, warning_mock):
        result = _run_execute_on_instance(None, 'https://scm', {}, 'ls', [], None)
        warning_mock.assert_called_once_with("%s", mock.ANY)
        self.assertEqual(result['instance'], 'default')

    @mock.patch(_MODULE + '.logger.debug')
    @mock.patch(_MODULE + '.logger.warning')
    @mock.patch(_MODULE + '._execute_command_on_instance', side_effect=ValueError('unexpected'))
    def test_unexpected_exception_returns_failed_result(self, _execute_mock, warning_mock, debug_mock):
        result = _run_execute_on_instance(None, 'https://scm', {}, 'ls', [], None)
        debug_mock.assert_called_once_with(
            "An unexpected error occurred while submitting the command.", exc_info=True)
        warning_mock.assert_called_once_with(
            "%s", "An unexpected error occurred while submitting the command.")
        self.assertEqual(
            result,
            {
                'instance': 'default',
                'status': 'failed',
                'error': 'An unexpected error occurred while submitting the command.',
            })


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

    @mock.patch(_MODULE + '.list_instances', return_value=[_instance('i1'), _instance('i2')])
    def test_duplicate_instances_are_removed_preserving_order(self, _list_mock):
        self.assertEqual(
            _resolve_target_instances(self.cmd, 'rg', 'app', 'i2,i1,i2,i1', None),
            ['i2', 'i1'])

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

    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=False)
    @mock.patch('requests.post', autospec=True)
    def test_request_verifies_certificates_by_default(self, post_mock, _disable_verify):
        post_mock.return_value = mock.Mock(status_code=202, text='')
        _execute_command_on_instance('https://scm', {}, {}, 'ls')
        self.assertTrue(post_mock.call_args.kwargs['verify'])

    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=True)
    @mock.patch('requests.post', autospec=True)
    def test_request_honors_disabled_certificate_verification(self, post_mock, _disable_verify):
        post_mock.return_value = mock.Mock(status_code=202, text='')
        _execute_command_on_instance('https://scm', {}, {}, 'ls')
        self.assertFalse(post_mock.call_args.kwargs['verify'])

    @mock.patch('requests.post', autospec=True)
    def test_server_error_raises_response_error_with_message(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=500, text='{"Message": "Internal Error"}')
        with self.assertRaisesRegex(AzureResponseError, "Internal Error"):
            _execute_command_on_instance('https://scm', {}, {}, 'ls')

    @mock.patch('requests.post', autospec=True)
    def test_server_error_with_empty_body_uses_fallback_message(self, post_mock):
        post_mock.return_value = mock.Mock(status_code=500, text='')
        with self.assertRaisesRegex(AzureResponseError, "could not be completed"):
            _execute_command_on_instance('https://scm', {}, {}, 'ls')

    @mock.patch('requests.post', autospec=True)
    def test_non_202_responses_preserve_server_message(self, post_mock):
        for status_code in (400, 403, 404, 500, 503):
            with self.subTest(status_code=status_code):
                post_mock.return_value = mock.Mock(
                    status_code=status_code,
                    text='{"Message": "request rejected"}')
                with self.assertRaisesRegex(AzureResponseError, "request rejected"):
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

    @mock.patch(_MODULE + '.logger.debug')
    @mock.patch(_MODULE + '.logger.warning')
    def test_websocket_error_is_sanitized_and_closes_session(self, warning_mock, debug_mock):
        import threading
        ws = mock.Mock()
        ws.recv_data.side_effect = websocket.WebSocketProtocolException('invalid frame details')
        closed = threading.Event()
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        with mock.patch('sys.stdout', io.StringIO()):
            _read_from_server(ws, closed, decoder)
        warning_mock.assert_called_once_with("Shell session closed unexpectedly.")
        debug_mock.assert_called_once_with(
            "Shell session receive error: %s", mock.ANY, exc_info=True)
        self.assertTrue(closed.is_set())

    @mock.patch(_MODULE + '.logger.debug')
    @mock.patch(_MODULE + '.logger.warning')
    def test_unexpected_reader_error_does_not_escape_background_thread(self, warning_mock, debug_mock):
        import threading
        ws = mock.Mock()
        ws.recv_data.side_effect = RuntimeError('internal details')
        closed = threading.Event()
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        with mock.patch('sys.stdout', io.StringIO()):
            _read_from_server(ws, closed, decoder)
        warning_mock.assert_called_once_with("Shell session closed unexpectedly.")
        debug_mock.assert_called_once_with(
            "Unexpected shell session receive error: %s", mock.ANY, exc_info=True)
        self.assertTrue(closed.is_set())

    @mock.patch(_MODULE + '.logger.debug')
    @mock.patch(_MODULE + '.logger.warning')
    def test_connection_closed_is_silent_when_cleanup_has_not_started(self, warning_mock, debug_mock):
        import threading
        ws = mock.Mock()
        ws.recv_data.side_effect = websocket.WebSocketConnectionClosedException('closed')
        closed = threading.Event()
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        _read_from_server(ws, closed, decoder)
        warning_mock.assert_not_called()
        debug_mock.assert_not_called()
        self.assertTrue(closed.is_set())

    @mock.patch(_MODULE + '.logger.debug')
    @mock.patch(_MODULE + '.logger.warning')
    def test_connection_closed_is_silent_when_cleanup_is_in_progress(self, warning_mock, debug_mock):
        ws = mock.Mock()
        ws.recv_data.side_effect = websocket.WebSocketConnectionClosedException('closed')
        closed = mock.Mock()
        closed.is_set.side_effect = [False, True]
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        _read_from_server(ws, closed, decoder)
        warning_mock.assert_not_called()
        debug_mock.assert_not_called()
        closed.set.assert_called_once_with()


class NonWindowsTerminalTest(unittest.TestCase):
    """Validate Unix terminal state cleanup without requiring a Unix test host."""

    def test_terminal_setup_errors_are_sanitized(self):
        for failure_stage in ('attributes', 'signal', 'raw-mode'):
            with self.subTest(failure_stage=failure_stage):
                termios_mock = mock.Mock(TCSADRAIN=1)
                tty_mock = mock.Mock()
                signal_mock = mock.Mock(SIGWINCH=object())
                signal_mock.getsignal.return_value = object()
                select_mock = mock.Mock()
                if failure_stage == 'attributes':
                    termios_mock.tcgetattr.side_effect = OSError('terminal details')
                elif failure_stage == 'signal':
                    signal_mock.signal.side_effect = ValueError('signal details')
                else:
                    termios_mock.tcgetattr.return_value = object()
                    tty_mock.setraw.side_effect = OSError('raw mode details')

                with mock.patch.dict('sys.modules', {
                        'termios': termios_mock,
                        'tty': tty_mock,
                        'signal': signal_mock,
                        'select': select_mock,
                }), mock.patch('sys.stdin.fileno', return_value=7):
                    with self.assertRaisesRegex(
                            CLIInternalError,
                            "Could not configure the local terminal for interactive shell mode"):
                        _send_to_server_non_windows(mock.Mock(), mock.Mock())

    def test_terminal_settings_and_resize_handler_are_restored(self):
        fd = 7
        old_settings = object()
        old_winch_handler = object()
        sigwinch = object()
        termios_mock = mock.Mock(TCSADRAIN=1)
        termios_mock.tcgetattr.return_value = old_settings
        tty_mock = mock.Mock()
        signal_mock = mock.Mock(SIGWINCH=sigwinch)
        signal_mock.getsignal.return_value = old_winch_handler
        select_mock = mock.Mock()
        closed = mock.Mock()
        closed.is_set.return_value = True

        with mock.patch.dict('sys.modules', {
                'termios': termios_mock,
                'tty': tty_mock,
                'signal': signal_mock,
                'select': select_mock,
        }), mock.patch('sys.stdin.fileno', return_value=fd):
            _send_to_server_non_windows(mock.Mock(), closed)

        tty_mock.setraw.assert_called_once_with(fd)
        self.assertEqual(signal_mock.signal.call_count, 2)
        self.assertEqual(signal_mock.signal.call_args_list[0].args[0], sigwinch)
        self.assertTrue(callable(signal_mock.signal.call_args_list[0].args[1]))
        self.assertEqual(
            signal_mock.signal.call_args_list[1],
            mock.call(sigwinch, old_winch_handler))
        termios_mock.tcsetattr.assert_called_once_with(fd, termios_mock.TCSADRAIN, old_settings)


class WindowsTerminalTest(unittest.TestCase):
    """Validate Windows console setup and cleanup without requiring a Windows console."""

    @staticmethod
    def _console_modules(get_mode_result=True, set_mode_result=True):
        kernel32 = mock.Mock()
        kernel32.GetStdHandle.return_value = 12
        kernel32.GetConsoleMode.return_value = get_mode_result
        kernel32.SetConsoleMode.return_value = set_mode_result
        old_mode = mock.Mock(value=7)
        ctypes_mock = mock.Mock()
        ctypes_mock.windll.kernel32 = kernel32
        ctypes_mock.c_uint32.return_value = old_mode
        ctypes_mock.byref.side_effect = lambda value: value
        return ctypes_mock, mock.Mock(), kernel32

    def test_console_setup_errors_are_sanitized(self):
        for get_mode_result, set_mode_result in ((False, True), (True, False)):
            with self.subTest(get_mode_result=get_mode_result, set_mode_result=set_mode_result):
                ctypes_mock, msvcrt_mock, _kernel32 = self._console_modules(
                    get_mode_result, set_mode_result)
                with mock.patch.dict('sys.modules', {
                        'ctypes': ctypes_mock,
                        'msvcrt': msvcrt_mock,
                }):
                    with self.assertRaisesRegex(
                            CLIInternalError,
                            "Could not configure the local terminal for interactive shell mode"):
                        _send_to_server_windows(mock.Mock(), mock.Mock())

    def test_console_mode_is_restored(self):
        ctypes_mock, msvcrt_mock, kernel32 = self._console_modules()
        closed = mock.Mock()
        closed.is_set.return_value = True
        with mock.patch.dict('sys.modules', {
                'ctypes': ctypes_mock,
                'msvcrt': msvcrt_mock,
        }):
            _send_to_server_windows(mock.Mock(), closed)

        self.assertEqual(
            kernel32.SetConsoleMode.call_args_list,
            [mock.call(12, 6), mock.call(12, 7)])


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
            mock.patch('sys.stdin.isatty', return_value=True),
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

    def test_kudu_target_is_appended_and_url_encoded_with_shell(self):
        _start_shell_session('https://scm.example', {}, shell='/bin/sh', target='kudu')
        self.assertEqual(
            self.create_conn.call_args.args[0],
            'wss://scm.example/exec/shell?target=kudu&shell=%2Fbin%2Fsh')

    @mock.patch(_MODULE + '.logger.warning')
    def test_connection_message_reflects_app_target(self, warning):
        _start_shell_session('https://scm.example', {})
        warning.assert_any_call("Connecting to the %s container...", 'web app')

    @mock.patch(_MODULE + '.logger.warning')
    def test_connection_message_reflects_kudu_target(self, warning):
        _start_shell_session('https://scm.example', {}, target='kudu')
        warning.assert_any_call("Connecting to the %s container...", 'Kudu')

    def test_cookies_are_formatted_into_cookie_string(self):
        _start_shell_session('https://scm.example', {}, cookies={'ARRAffinity': 'abc'})
        self.assertEqual(self.create_conn.call_args.kwargs['cookie'], 'ARRAffinity=abc')

    def test_no_cookies_sends_none(self):
        _start_shell_session('https://scm.example', {})
        self.assertIsNone(self.create_conn.call_args.kwargs['cookie'])

    def test_redirected_stdin_raises_validation_error_before_connecting(self):
        with mock.patch('sys.stdin.isatty', return_value=False):
            with self.assertRaisesRegex(ValidationError, "requires an interactive terminal"):
                _start_shell_session('https://scm.example', {})
        self.create_conn.assert_not_called()

    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=False)
    def test_connection_is_thread_safe_and_verifies_certificates_by_default(self, _disable_verify):
        _start_shell_session('https://scm.example', {})
        self.assertTrue(self.create_conn.call_args.kwargs['enable_multithread'])
        self.assertEqual(
            self.create_conn.call_args.kwargs['sslopt'],
            {'cert_reqs': ssl.CERT_REQUIRED})

    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=True)
    def test_connection_honors_disabled_certificate_verification(self, _disable_verify):
        _start_shell_session('https://scm.example', {})
        self.assertEqual(
            self.create_conn.call_args.kwargs['sslopt'],
            {'cert_reqs': ssl.CERT_NONE})

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
