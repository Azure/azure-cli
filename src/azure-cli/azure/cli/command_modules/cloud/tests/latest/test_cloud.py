# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# When tested locally, please use 'azdev test cloud -a "-n 1" to run in serial'

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.decorators import serial_test


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

    @serial_test()
    def test_cloud_set_AzureCloud(self):
        self.cmd('az cloud set -n AzureCloud')
        self.cmd('az cloud show -n AzureCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_AzureChinaCloud(self):
        self.cmd('az cloud set -n AzureChinaCloud')
        self.cmd('az cloud show -n AzureChinaCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_AzureUSGovernment(self):
        self.cmd('az cloud set -n AzureUSGovernment')
        self.cmd('az cloud show -n AzureUSGovernment', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_AzureGermanCloud(self):
        self.cmd('az cloud set -n AzureGermanCloud')
        self.cmd('az cloud show -n AzureGermanCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_azurecloud(self):
        self.cmd('az cloud set -n azurecloud')
        self.cmd('az cloud show -n AzureCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_azurechinacloud(self):
        self.cmd('az cloud set -n azurechinacloud')
        self.cmd('az cloud show -n AzureChinaCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_azureusgovernment(self):
        self.cmd('az cloud set -n azureusgovernment')
        self.cmd('az cloud show -n AzureUSGovernment', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_azuregermancloud(self):
        self.cmd('az cloud set -n azuregermancloud')
        self.cmd('az cloud show -n AzureGermanCloud', checks=[self.check('isActive', True)])

    @serial_test()
    def test_cloud_set_unregistered_cloud_name(self):
        self.cmd('az cloud set -n azCloud', expect_failure=True)


class SubscriptionSuppressionTest(ScenarioTest):

    def test_subscription_suppression(self):
        from knack.util import CLIError
        self.cmd('az cloud list')

        # this should fail with an "unrecognized argument" error
        with self.assertRaisesRegex(SystemExit, '2'):
            self.cmd('az cloud list --subscription foo')
