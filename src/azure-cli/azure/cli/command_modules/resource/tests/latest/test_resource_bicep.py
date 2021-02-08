import unittest
import mock

from azure.cli.command_modules.resource._bicep import ensure_bicep_installation


class TestBicep(unittest.TestCase):
    @mock.patch("os.path.isfile")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_bicep_latest_release_tag")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("azure.cli.command_modules.resource._bicep._logger.warning")
    def test_ensure_bicep_installation_check_upgrade(
        self, warning_mock, _get_bicep_installed_version_stub, get_bicep_latest_release_tag_stub, isfile_stub
    ):
        # Arrange.
        _get_bicep_installed_version_stub.return_value = "1.0.0"
        get_bicep_latest_release_tag_stub.return_value = "v2.0.0"
        isfile_stub.return_value = True

        # Act.
        installation_path = ensure_bicep_installation(check_upgrade=True)

        # Assert.
        warning_mock.assert_called_once_with(
            'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
            "v2.0.0",
        )
        self.assertIsNotNone(installation_path)

    @mock.patch("os.path.isfile")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.dirname")
    def test_ensure_bicep_installation_skip_download_if_installed_version_matches_release_tag(
        self, dirname_mock, _get_bicep_installed_version_stub, isfile_stub
    ):
        # Arrange.
        _get_bicep_installed_version_stub.return_value = "0.1.0"
        isfile_stub.return_value = True

        # Act.
        installation_path = ensure_bicep_installation(release_tag='v0.1.0')

        # Assert
        dirname_mock.assert_not_called()
        self.assertIsNotNone(installation_path)