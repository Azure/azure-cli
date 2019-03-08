# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest
from knack.util import CLIError

class CloudTests(ScenarioTest):
    def test_cloud_set_AzureCloud(self):
        self.cmd('az cloud set -n AzureCloud')

    def test_cloud_set_AzureChinaCloud(self):
        self.cmd('az cloud set -n AzureChinaCloud')

    def test_cloud_set_AzureUSGovernment(self):
        self.cmd('az cloud set -n AzureUSGovernment')

    def test_cloud_set_AzureGermanCloud(self):
        self.cmd('az cloud set -n AzureGermanCloud')

    def test_cloud_set_azurecloud(self):
        self.cmd('az cloud set -n azurecloud')

    def test_cloud_set_azurechinacloud(self):
        self.cmd('az cloud set -n azurechinacloud')

    def test_cloud_set_azureusgovernment(self):
        self.cmd('az cloud set -n azureusgovernment')

    def test_cloud_set_azuregermancloud(self):
        self.cmd('az cloud set -n azuregermancloud')

    def test_cloud_set_unregistered_cloud_name(self):
        with self.assertRaisesRegexp(CLIError, "The cloud 'azCloud' is not registered."):
            self.cmd('az cloud set -n azCloud')
