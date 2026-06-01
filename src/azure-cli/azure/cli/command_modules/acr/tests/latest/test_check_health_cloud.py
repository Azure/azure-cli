# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.acr.check_health import _get_health_check_image


class TestGetHealthCheckImage(unittest.TestCase):
    """Unit tests for cloud-aware MCR image resolution in check-health."""

    def _make_cmd(self, cloud_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx.cloud.name = cloud_name
        return cmd

    def test_default_cloud(self):
        cmd = self._make_cmd("AzureCloud")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.com/mcr/hello-world:latest")

    def test_ussec_cloud(self):
        cmd = self._make_cmd("USSec")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.scloud/mcr/hello-world:latest")

    def test_usnat_cloud(self):
        cmd = self._make_cmd("USNat")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.eaglex.ic.gov/mcr/hello-world:latest")

    def test_ussec_case_insensitive(self):
        cmd = self._make_cmd("ussec")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.scloud/mcr/hello-world:latest")

    def test_usnat_case_insensitive(self):
        cmd = self._make_cmd("USNAT")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.eaglex.ic.gov/mcr/hello-world:latest")

    def test_azure_us_government(self):
        # Fairfax uses the standard MCR endpoint
        cmd = self._make_cmd("AzureUSGovernment")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.com/mcr/hello-world:latest")

    def test_azure_china_cloud(self):
        # China cloud uses the standard MCR endpoint
        cmd = self._make_cmd("AzureChinaCloud")
        self.assertEqual(_get_health_check_image(cmd), "mcr.microsoft.com/mcr/hello-world:latest")


if __name__ == '__main__':
    unittest.main()
