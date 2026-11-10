# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from contextlib import contextmanager
from subprocess import CalledProcessError
import unittest
from unittest import mock

from knack.util import CLIError

from azure.cli.command_modules.acr import check_health
from azure.cli.command_modules.acr._errors import HELM_COMMAND_ERROR


class TestAcrCheckHealth(unittest.TestCase):
    warning = 'WARNING: kubeconfig is group-readable'
    rejection = 'Error: unknown flag: --client'
    failure = 'Error: version probe failed'

    @contextmanager
    def _helm_processes(self, responses, discovery_error=None):
        responses = dict(responses)

        def start_process(command_parts, **kwargs):
            args = tuple(command_parts[1:])
            self.assertIn(args, responses, 'Unexpected Helm invocation')
            response = responses.pop(args)
            if isinstance(response, Exception):
                raise response
            exit_code, stdout, stderr = response
            process = mock.Mock(returncode=exit_code)
            process.communicate.return_value = (stdout.encode('UTF-8'), stderr.encode('UTF-8'))
            return process

        discovery = (None, discovery_error) if discovery_error else ('helm', None)
        with mock.patch.object(check_health, 'get_helm_command', return_value=discovery), \
                mock.patch('subprocess.Popen', side_effect=start_process):
            yield

    def _assert_helm_error(self, responses, ignore_errors, detail, discovery_error=None):
        with self._helm_processes(responses, discovery_error):
            if ignore_errors:
                with self.assertLogs(check_health.logger, level='WARNING') as logs:
                    check_health._get_helm_version(ignore_errors)
                diagnostic = '\n'.join(logs.output)
            else:
                with self.assertRaises(CLIError) as raised:
                    check_health._get_helm_version(ignore_errors)
                diagnostic = str(raised.exception)
        category = 'HELM_COMMAND_ERROR' if discovery_error else 'HELM_VERSION_ERROR'
        self.assertIn(category, diagnostic)
        self.assertIn(detail, diagnostic)
        self.assertNotIn('Helm version:', diagnostic)

    def test_legacy_client_only_versions(self):
        for version, output in (
                ('2.11.0', 'Client: &version.Version{SemVer:"v2.11.0"}'),
                ('3.19.0', 'version.BuildInfo{Version:"v3.19.0"}')):
            with self.subTest(version=version), self._helm_processes({
                    ('version', '--client'): (0, output, ''),
                    ('version',): (1, '', 'Error: could not connect to Tiller')}):
                with self.assertLogs(check_health.logger, level='WARNING') as logs:
                    check_health._get_helm_version(False)
                diagnostic = '\n'.join(logs.output)
                self.assertIn('Helm version: ' + version, diagnostic)
                self.assertNotIn('HELM_VERSION_ERROR', diagnostic)

    def test_removed_client_flag_falls_back_to_modern_version(self):
        for ignore_errors in (False, True):
            for prefix in ('', self.warning + '\n'):
                with self.subTest(ignore_errors=ignore_errors, prefix=prefix), self._helm_processes({
                        ('version', '--client'): (1, '', prefix + self.rejection),
                        ('version',): (0, 'version.BuildInfo{Version:"v4.1.4"}', '')}):
                    with self.assertLogs(check_health.logger, level='WARNING') as logs:
                        check_health._get_helm_version(ignore_errors)
                    diagnostic = '\n'.join(logs.output)
                    self.assertIn('Helm version: 4.1.4', diagnostic)
                    self.assertNotIn('HELM_VERSION_ERROR', diagnostic)
                    self.assertNotIn(self.rejection, diagnostic)

    def test_failed_fallback_respects_error_policy(self):
        for ignore_errors in (False, True):
            with self.subTest(ignore_errors=ignore_errors):
                self._assert_helm_error({
                    ('version', '--client'): (1, '', self.rejection),
                    ('version',): (1, '', self.warning + '\n' + self.failure)
                }, ignore_errors, self.failure)

    def test_unrelated_failures_do_not_retry(self):
        for ignore_errors in (False, True):
            for stderr in (self.failure, self.warning + '\n' + self.failure, ''):
                with self.subTest(ignore_errors=ignore_errors, stderr=stderr):
                    self._assert_helm_error({
                        ('version', '--client'): (1, '', stderr)
                    }, ignore_errors, stderr)

    def test_version_launch_exceptions_respect_error_policy(self):
        for ignore_errors in (False, True):
            for error in (OSError('version launch failed'),
                          CalledProcessError(1, ['helm', 'version', '--client'])):
                with self.subTest(ignore_errors=ignore_errors, error=error):
                    self._assert_helm_error({
                        ('version', '--client'): error
                    }, ignore_errors, str(error))

    def test_successful_warning_remains_visible_without_retry(self):
        # Even a successful warning mentioning the flag must not trigger fallback.
        warning = self.warning + '\n' + self.rejection
        with self._helm_processes({
                ('version', '--client'): (0, 'version.BuildInfo{Version:"v3.19.0"}', warning)}):
            with self.assertLogs(check_health.logger, level='WARNING') as logs:
                check_health._get_helm_version(False)
        diagnostic = '\n'.join(logs.output)
        self.assertIn('Helm version: 3.19.0', diagnostic)
        self.assertIn(warning, diagnostic)
        self.assertNotIn('HELM_VERSION_ERROR', diagnostic)

    def test_obsolete_version_respects_error_policy(self):
        for ignore_errors in (False, True):
            with self.subTest(ignore_errors=ignore_errors), self._helm_processes({
                    ('version', '--client'): (0, 'Client: &version.Version{SemVer:"v2.10.0"}', '')}):
                with self.assertLogs(check_health.logger, level='WARNING') as logs:
                    if ignore_errors:
                        check_health._get_helm_version(ignore_errors)
                        error = '\n'.join(logs.output)
                    else:
                        with self.assertRaises(CLIError) as raised:
                            check_health._get_helm_version(ignore_errors)
                        error = str(raised.exception)
                self.assertIn('Helm version: 2.10.0', '\n'.join(logs.output))
                self.assertIn('HELM_VERSION_ERROR', error)
                self.assertIn(check_health.MIN_HELM_VERSION, error)

    def test_missing_helm_respects_error_policy(self):
        for ignore_errors in (False, True):
            with self.subTest(ignore_errors=ignore_errors):
                self._assert_helm_error({}, ignore_errors, 'HELM_COMMAND_ERROR', HELM_COMMAND_ERROR)

    def test_command_continues_after_ignored_helm_failure(self):
        for ignore_errors in (False, True):
            with self.subTest(ignore_errors=ignore_errors), \
                    mock.patch('azure.cli.core.util.in_cloud_console', return_value=False), \
                    mock.patch.object(check_health, '_get_docker_status_and_version'), \
                    self._helm_processes({
                        ('version', '--client'): (1, '', self.warning + '\n' + self.failure)}):
                with self.assertLogs(check_health.logger, level='WARNING') as logs:
                    if ignore_errors:
                        check_health.acr_check_health(cmd=mock.Mock(), ignore_errors=True, yes=True)
                    else:
                        with self.assertRaises(CLIError) as raised:
                            check_health.acr_check_health(cmd=mock.Mock(), ignore_errors=False, yes=True)
                        self.assertIn('HELM_VERSION_ERROR', str(raised.exception))
                diagnostic = '\n'.join(logs.output)
                if ignore_errors:
                    self.assertIn('HELM_VERSION_ERROR', diagnostic)
                    self.assertIn(self.failure, diagnostic)
                    self.assertIn(check_health.FAQ_MESSAGE, diagnostic)
                else:
                    self.assertNotIn(check_health.FAQ_MESSAGE, diagnostic)
