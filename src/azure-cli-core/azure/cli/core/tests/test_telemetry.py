# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock


class TestCoreTelemetry(unittest.TestCase):
    def test_suppress_all_exceptions(self):
        self._impl(Exception, 'fallback')
        self._impl(Exception, None)
        self._impl(ImportError, 'fallback_for_import_error')
        self._impl(None, None)

    def _impl(self, exception_to_raise, fallback_return):
        from azure.cli.core.decorators import suppress_all_exceptions

        @suppress_all_exceptions(fallback_return=fallback_return)
        def _error_fn():
            if not exception_to_raise:
                return 'positive result'
            else:
                raise exception_to_raise()

        if not exception_to_raise:
            self.assertEqual(_error_fn(), 'positive result')
        else:
            self.assertEqual(_error_fn(), fallback_return)

    def test_extract_parameters_correctly(self):
        from azure.cli.core.commands import AzCliCommandInvoker
        args = ['vm', 'user', 'update', '-g', 'rg', '-n', 'vm1', '-u', 'user',
                '--ssh-key-value', '-----BEGIN PRIVATE KEY-----']
        self.assertEqual(['-g', '-n', '-u', '--ssh-key-value'], AzCliCommandInvoker._extract_parameter_names(args))

        args = ['vm', 'create', '--resource-group-name', 'rg', '--name', 'vm1', '--image', 'centos']
        self.assertEqual(['--resource-group-name', '--name', '--image'], AzCliCommandInvoker._extract_parameter_names(args))

        args = ['vm', 'show', '-g', 'rg', '--name', 'vm1', '-d', '--debug']
        self.assertEqual(['-g', '--name', '-d', '--debug'], AzCliCommandInvoker._extract_parameter_names(args))

    def test_cloud_forbid_telemetry(self):
        from unittest import mock
        from azure.cli.core import telemetry
        from azure.cli.core.mock import DummyCli
        from knack.completion import ARGCOMPLETE_ENV_NAME

        az_cli = DummyCli()
        telemetry.set_application(az_cli, ARGCOMPLETE_ENV_NAME)
        # mock user turns off telemetry
        with mock.patch('knack.config.CLIConfig.getboolean', return_value=False):
            self.assertFalse(telemetry.is_telemetry_enabled())
        # mock user turns on telemetry
        with mock.patch('knack.config.CLIConfig.getboolean', return_value=True):
            self.assertTrue(telemetry.is_telemetry_enabled())
            # mock to add current cloud name in CLOUDS_FORBIDDING_TELEMETRY
            with mock.patch('azure.cli.core.cloud.CLOUDS_FORBIDDING_TELEMETRY', [az_cli.cloud.name]):
                self.assertFalse(telemetry.is_telemetry_enabled())

    @mock.patch('azure.cli.core.util.get_az_version_string')
    def test_show_version_sets_telemetry_params(self, mock_get_version):
        """Test show_version telemetry state is same regardless of available updates."""
        from azure.cli.core.mock import DummyCli
        from azure.cli.core import telemetry
        from knack.completion import ARGCOMPLETE_ENV_NAME

        mock_get_version.return_value = ("azure-cli 2.80.0", ["core", "extension1"])

        telemetry.start()

        cli = DummyCli()
        telemetry.set_application(cli, ARGCOMPLETE_ENV_NAME)

        cli.show_version()

        session = telemetry._session
        self.assertEqual(session.command, "")
        self.assertEqual(session.parameters, ["--version"])
        self.assertIsNone(session.raw_command)

    @mock.patch('azure.cli.core.util.get_az_version_string')
    def test_command_preserve_casing_telemetry(self, mock_get_version):
        """Test telemetry captures command preserve casing during actual command invocation."""
        from azure.cli.core import telemetry
        from azure.cli.core.mock import DummyCli
        from knack.completion import ARGCOMPLETE_ENV_NAME

        mock_get_version.return_value = ("azure-cli 2.80.0", ["core", "extension1"])

        test_cases = [
            (["version"], "version"),
            (["VERSION"], "VERSION"),
            (["vm", "list"], "vm list"),
            (["Vm", "List"], "Vm List"),
        ]

        for command_args, expected_casing in test_cases:
            with self.subTest(command_args=command_args):
                cli = DummyCli()
                telemetry.set_application(cli, ARGCOMPLETE_ENV_NAME)
                telemetry.start()

                try:
                    cli.invoke(command_args)
                except SystemExit:
                    pass
                except Exception:
                    pass

                # Verify the telemetry session preserves casing
                session = telemetry._session
                self.assertEqual(session.command_preserve_casing, expected_casing)

                azure_cli_props = session._get_azure_cli_properties()

                self.assertIn('Context.Default.AzureCLI.CommandPreserveCasing', azure_cli_props)
                self.assertEqual(azure_cli_props['Context.Default.AzureCLI.CommandPreserveCasing'], 
                                 expected_casing)
