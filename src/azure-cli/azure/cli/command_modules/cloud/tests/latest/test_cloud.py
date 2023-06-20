# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# When tested locally, please use 'azdev test cloud -a "-n 1" to run in serial'

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.decorators import serial_test


class CloudTests(ScenarioTest):
    def setUp(self):
        super().setUp()
        self.cloudname = self.cmd('az cloud show').get_output_in_json().get('name')

    def tearDown(self):
        # cli_ctx cloud name is used to check with the cloud name to set
        # If both are same, it will skip the switch
        # The test case cli_ctx isn't change even when the cloud is really changed
        # So here set the cli_ctx cloud name to empty to enforce cloud to switch
        super().tearDown()
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

    @serial_test()
    def test_cloud_list_profiles(self):
        result = self.cmd('cloud list-profiles').get_output_in_json()
        assert result == [
            "latest",
            "2017-03-09-profile",
            "2018-03-01-hybrid",
            "2019-03-01-hybrid",
            "2020-09-01-hybrid"
        ]

    @serial_test()
    def test_cloud_scenario(self):
        self.kwargs['name'] = 'mycloud'

        # NOTE: As cli_ctx is copied during `az cloud set`, the original cli_ctx.cloud.name won't be changed.
        # Thus, commands such as `az login`, `az cloud show` or `az cloud unregister` won't work
        # as expected because it will still operate on the previously selected cloud.

        # Make sure we have a clean start
        try:
            self.cli_ctx.cloud.name = 'AzureCloud'
            self.cmd('cloud unregister --name {name}')
        except Exception as ex:
            print(ex)

        # Register a cloud using cloud discovery
        self.cmd('cloud register --name {name} --endpoint-resource-manager https://management.azure.com/')
        result = self.cmd('az cloud show --name {name}').get_output_in_json()
        assert result['name'] == 'mycloud'
        assert result['endpoints']['activeDirectory'] == 'https://login.microsoftonline.com/'
        assert result['endpoints']['management'] == 'https://management.azure.com/'

        # Update the cloud
        self.cmd('cloud update --name {name} --endpoint-active-directory https://login.myendpoint.com/ '
                 '--endpoint-management https://management.myendpoint.com/')
        result = self.cmd('cloud show --name {name}').get_output_in_json()
        assert result['endpoints']['activeDirectory'] == 'https://login.myendpoint.com/'
        assert result['endpoints']['management'] == 'https://management.myendpoint.com/'

        # TODO: Test all arguments of `az cloud update`

        self.cmd('cloud set --name {name} --profile 2020-09-01-hybrid')
        self.cli_ctx.cloud.name = self.kwargs['name']

        self.cmd('cloud show', checks=[self.check('name', '{name}'),
                                       self.check('isActive', True)])
        self.cmd('cloud show --name {name}', checks=[self.check('name', '{name}'),
                                                     self.check('isActive', True)])

        # Unregister the cloud
        self.cmd('cloud set --name AzureCloud')
        self.cli_ctx.cloud.name = 'AzureCloud'
        self.cmd('cloud unregister --name {name}')

        # The cloud no longer exists
        self.cmd('cloud show --name {name}', expect_failure=True)

        # TODO: test manual cloud registration by specifying all arguments, instead of using cloud discovery


class SubscriptionSuppressionTest(ScenarioTest):

    def test_subscription_suppression(self):
        from knack.util import CLIError
        self.cmd('az cloud list')

        # this should fail with an "unrecognized argument" error
        with self.assertRaisesRegex(SystemExit, '2'):
            self.cmd('az cloud list --subscription foo')
