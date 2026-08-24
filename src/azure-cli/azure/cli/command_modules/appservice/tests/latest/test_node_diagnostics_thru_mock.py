# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.appservice.node_diagnostics import (
    _get_collection_command,
    _parse_node_processes,
    _select_process,
    collect_cpu_profiler_trace,
)

_MODULE = 'azure.cli.command_modules.appservice.node_diagnostics'


def _get_test_cmd():
    from azure.cli.core import AzCommandsLoader
    from azure.cli.core.commands import AzCliCommand
    from azure.cli.core.mock import DummyCli

    cli_ctx = DummyCli()
    loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_APPSERVICE)
    cmd = AzCliCommand(loader, 'test', None)
    cmd.command_kwargs = {'resource_type': ResourceType.MGMT_APPSERVICE}
    cmd.cli_ctx = cli_ctx
    return cmd


class NodeDiagnosticsTest(unittest.TestCase):

    def test_parse_node_processes_omits_shell_parent(self):
        output = (
            '10 1 sh sh -c node server.js\n'
            '11 10 node node server.js\n'
            '20 1 python python app.py\n')

        processes = _parse_node_processes(output)

        self.assertEqual([11], [process['pid'] for process in processes])

    def test_select_process_rejects_unknown_pid(self):
        processes = [{'pid': 11, 'parentPid': 1, 'command': 'node', 'args': 'node server.js'}]

        with self.assertRaisesRegex(ValidationError, 'Valid process IDs: 11'):
            _select_process(processes, 12)

    def test_get_collection_command_uses_kudu_scripts(self):
        session = mock.Mock()
        response = mock.Mock(status_code=200)
        response.json.return_value = {'ExitCode': 0, 'Output': 'generated command'}
        session.post.return_value = response

        command = _get_collection_command(
            session, 'https://app.scm.azurewebsites.net', 'cpu', 11, 30,
            '/home/LogFiles/diagnostics/cpu/profile.cpuprofile', 60)

        self.assertEqual('generated command', command)
        payload = session.post.call_args.kwargs['json']
        self.assertIn('/opt/Kudu/wwwroot/js/diagnostics/stacks.js', payload['command'])
        self.assertIn('DiagnosticStacks.node.cpu.collectCmd(11,30', payload['command'])
        self.assertIn('wrapNodeDiagnosticCollectionCommand', payload['command'])

    @mock.patch(_MODULE + '._run_analyzer')
    @mock.patch(_MODULE + '._run_shell_command')
    @mock.patch(_MODULE + '._get_collection_command', return_value='collect')
    @mock.patch(_MODULE + '._select_process', return_value={
        'pid': 11, 'parentPid': 1, 'command': 'node', 'args': 'node server.js'})
    @mock.patch(_MODULE + '._discover_node_processes', return_value=[])
    @mock.patch(_MODULE + '._ensure_diagnostics_available')
    @mock.patch(_MODULE + '._create_http_session', return_value=mock.Mock())
    @mock.patch(_MODULE + '.get_scm_site_headers', return_value={'Authorization': 'Basic test'})
    @mock.patch(_MODULE + '._get_scm_url', return_value='https://app.scm.azurewebsites.net')
    @mock.patch(_MODULE + '._select_instance', return_value='abc123')
    @mock.patch(_MODULE + '.is_linux_webapp', return_value=True)
    @mock.patch(_MODULE + '._generic_site_operation', return_value=mock.Mock())
    def test_cpu_collection_returns_structured_urls(self, _site, _linux, _instance, _scm, _headers,
                                                    _session, _available, _discover, _process,
                                                    _get_command, run_shell, run_analyzer):
        result = collect_cpu_profiler_trace(
            _get_test_cmd(), 'rg', 'app', instance='abc123', process_id=11, duration=30)

        self.assertEqual('cpuProfile', result['diagnosticType'])
        self.assertEqual('ready', result['status'])
        self.assertEqual(11, result['processId'])
        self.assertIn('/api/vfs/LogFiles/diagnostics/cpu/', result['artifactUrl'])
        self.assertIn('/cpuprofiling?instance=abc123', result['diagnosticsPageUrl'])
        run_shell.assert_called_once()
        run_analyzer.assert_called_once()

    @mock.patch(_MODULE + '.is_linux_webapp', return_value=True)
    @mock.patch(_MODULE + '._generic_site_operation', return_value=mock.Mock())
    def test_cpu_collection_rejects_invalid_duration(self, _site, _linux):
        with self.assertRaisesRegex(ValidationError, 'between 5 and 300'):
            collect_cpu_profiler_trace(_get_test_cmd(), 'rg', 'app', duration=4)


if __name__ == '__main__':
    unittest.main()