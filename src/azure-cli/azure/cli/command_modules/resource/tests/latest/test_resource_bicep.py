import unittest
import mock

from knack.util import CLIError
from azure.cli.command_modules.resource._bicep import ensure_bicep_installation, run_bicep_command


class TestBicep(unittest.TestCase):
    @mock.patch("os.path.isfile")
    def test_run_bicep_command_raise_error_if_not_installed_and_not_auto_install(self, isfile_stub):
        isfile_stub.return_value = False

        with self.assertRaisesRegex(CLIError, 'Bicep CLI not found. Install it now by running "az bicep install".'):
            run_bicep_command(["--version"], auto_install=False)

    @mock.patch("azure.cli.command_modules.resource._bicep._logger.warning")
    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("azure.cli.command_modules.resource._bicep.ensure_bicep_installation")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_bicep_latest_release_tag")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.isfile")
    def test_run_bicep_command_check_upgrade(
        self,
        isfile_stub,
        _get_bicep_installed_version_stub,
        get_bicep_latest_release_tag_stub,
        ensure_bicep_installation_mock,
        _run_command_mock,
        warning_mock,
    ):
        isfile_stub.return_value = True
        _get_bicep_installed_version_stub.return_value = "1.0.0"
        get_bicep_latest_release_tag_stub.return_value = "v2.0.0"

        run_bicep_command(["--version"], check_upgrade=True)

        warning_mock.assert_called_once_with(
            'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
            "v2.0.0",
        )

    @mock.patch("os.path.isfile")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.dirname")
    def test_ensure_bicep_installation_skip_download_if_installed_version_matches_release_tag(
        self, dirname_mock, _get_bicep_installed_version_stub, isfile_stub
    ):
        _get_bicep_installed_version_stub.return_value = "0.1.0"
        isfile_stub.return_value = True

        ensure_bicep_installation(release_tag="v0.1.0")

        dirname_mock.assert_not_called()