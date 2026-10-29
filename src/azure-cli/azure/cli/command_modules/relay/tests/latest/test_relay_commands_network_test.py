# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI Relay - NAMESPACE NETWORK RULE SET TEST DEFINITIONS

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class RelayNetworkCURDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_relay_network')
    def test_relay_network(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='relay-nwcli', length=20),
            'tags': 'tag1=value1',
            'sku': 'Standard',
            'ipmask1': '1.1.1.1',
            'ipmask2': '2.2.2.2'
        })

        # Check for the NameSpace name Availability
        self.cmd('relay namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'relay namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace
        self.cmd('relay namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('name', self.kwargs['namespacename'])])

        # Get NetworkRuleSet (default)
        self.cmd(
            'relay namespace network-rule-set show --resource-group {rg} --namespace-name {namespacename}')

        # add IP Rule
        networkRule = self.cmd(
            'relay namespace network-rule-set ip-rule add --resource-group {rg} --namespace-name {namespacename} '
            '--ip-rule ip-address={ipmask1} action=Allow '
            '--ip-rule ip-address={ipmask2} action=Allow').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 2)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(networkRule['ipRules'][1]['ipMask'] == '2.2.2.2')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])

        # Get list of IP rule
        networkRule = self.cmd(
            'relay namespace network-rule-set show --resource-group {rg} --namespace-name {namespacename}').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 2)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(networkRule['ipRules'][1]['ipMask'] == '2.2.2.2')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])

        # Add duplicate IP Rule should fail
        from azure.cli.core.azclierror import CLIError
        with self.assertRaises(CLIError):
            self.cmd(
                'relay namespace network-rule-set ip-rule add --resource-group {rg} --namespace-name {namespacename} '
                '--ip-rule ip-address={ipmask1} action=Allow')

        # Remove IPRule
        networkRule = self.cmd(
            'relay namespace network-rule-set ip-rule remove --resource-group {rg} --namespace-name {namespacename} '
            '--ip-rule ip-address={ipmask2}').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])

        # Update public network access to Disabled
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--public-network-access Disabled').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Disabled', networkRule['publicNetworkAccess'])

        # Update public network access back to Enabled
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--public-network-access Enabled').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])

        # Update default action to Deny
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--default-action Deny').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertEqual('Deny', networkRule['defaultAction'])

        # Update default action back to Allow
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--default-action Allow').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertEqual('Allow', networkRule['defaultAction'])

        # Enable trusted service access
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--trusted-service-access-enabled true').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['trustedServiceAccessEnabled'])

        # Disable trusted service access
        networkRule = self.cmd(
            'relay namespace network-rule-set update --resource-group {rg} --namespace-name {namespacename} '
            '--trusted-service-access-enabled false').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertFalse(networkRule['trustedServiceAccessEnabled'])

        # Delete Namespace
        self.cmd('relay namespace delete --resource-group {rg} --name {namespacename}')
