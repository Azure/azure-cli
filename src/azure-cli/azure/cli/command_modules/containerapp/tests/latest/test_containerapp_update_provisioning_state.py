# --------------------------------------------------------------------------------------------
# Copyright (c) nxt Engineering GmbH. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.containerapp.custom import (
    ContainerAppClient,
    ContainerAppsJobClient,
    update_containerapp_logic,
    update_containerappsjob_logic,
)

# flake8: noqa
# noqa
# pylint: skip-file


# `ContainerAppClient.update`/`ContainerAppsJobClient.update` return None when no_wait=True,
# so the post-update provisioningState check must short-circuit on `not no_wait` before
# indexing into that None result.
class UpdateProvisioningStateCheckTest(unittest.TestCase):
    @mock.patch("azure.cli.command_modules.containerapp.custom._validate_subscription_registered")
    @mock.patch.object(ContainerAppClient, "update", return_value=None)
    @mock.patch.object(ContainerAppClient, "show", return_value={"properties": {}})
    def test_containerapp_update_no_wait_does_not_raise(self, _show_mock, _update_mock, _validate_mock):
        cmd = mock.MagicMock()

        result = update_containerapp_logic(
            cmd=cmd, name="app1", resource_group_name="rg1", no_wait=True)

        self.assertIsNone(result)

    @mock.patch("azure.cli.command_modules.containerapp.custom._validate_subscription_registered")
    @mock.patch.object(ContainerAppsJobClient, "update", return_value=None)
    @mock.patch.object(ContainerAppsJobClient, "show", return_value={"properties": {}})
    def test_containerappjob_update_no_wait_does_not_raise(self, _show_mock, _update_mock, _validate_mock):
        cmd = mock.MagicMock()

        result = update_containerappsjob_logic(
            cmd=cmd, name="job1", resource_group_name="rg1", no_wait=True)

        self.assertIsNone(result)

    @mock.patch("azure.cli.command_modules.containerapp.custom._validate_subscription_registered")
    @mock.patch.object(ContainerAppClient, "update", return_value={"properties": {"provisioningState": "Waiting"}})
    @mock.patch.object(ContainerAppClient, "show", return_value={"properties": {}})
    def test_containerapp_update_without_no_wait_returns_response(self, _show_mock, update_mock, _validate_mock):
        cmd = mock.MagicMock()

        result = update_containerapp_logic(
            cmd=cmd, name="app1", resource_group_name="rg1", no_wait=False)

        self.assertEqual(result, update_mock.return_value)

    @mock.patch("azure.cli.command_modules.containerapp.custom._validate_subscription_registered")
    @mock.patch.object(ContainerAppsJobClient, "update", return_value={"properties": {"provisioningState": "Waiting"}})
    @mock.patch.object(ContainerAppsJobClient, "show", return_value={"properties": {}})
    def test_containerappjob_update_without_no_wait_returns_response(self, _show_mock, update_mock, _validate_mock):
        cmd = mock.MagicMock()

        result = update_containerappsjob_logic(
            cmd=cmd, name="job1", resource_group_name="rg1", no_wait=False)

        self.assertEqual(result, update_mock.return_value)


if __name__ == "__main__":
    unittest.main()
