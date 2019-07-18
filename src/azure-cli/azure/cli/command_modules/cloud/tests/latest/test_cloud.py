# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest


class CloudTests(ScenarioTest):
    def setUp(self):
        self.cloudname = self.cmd('az cloud show').get_output_in_json().get('name')

    def tearDown(self):
        # cli_ctx cloud name is used to check with the cloud name to set
        # If both are same, it will skip the switch
        # The test case cli_ctx isn't change even when the cloud is really changed
        # So here set the cli_ctx cloud name to empty to enforce cloud to switch
        self.cli_ctx.cloud.name = ''
        self.cmd('az cloud set -n ' + self.cloudname)

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
        self.cmd('az cloud set -n azCloud', expect_failure=True)


class SubscriptionSuppressionTest(ScenarioTest):

    def test_subscription_suppression(self):
        from knack.util import CLIError
        self.cmd('az cloud list')

        # this should fail with an "unrecognized argument" error
        with self.assertRaisesRegexp(SystemExit, '2'):
            self.cmd('az cloud list --subscription foo')
