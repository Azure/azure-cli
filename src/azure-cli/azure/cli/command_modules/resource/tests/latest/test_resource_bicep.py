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
        ensure_bicep_installation(check_upgrade=True)

        # Assert.
        warning_mock.assert_called_once_with(
            'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
            "v2.0.0",
        )


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == "https://api.github.com/repos/Azure/bicep/releases/latest":
        return MockResponse({"tag_name": "v2.0.0"}, 200)

    return MockResponse(None, 404)