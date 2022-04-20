# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI ServiceBus - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNamespaceMSITesting(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_sb_namespace_msi(self, resource_group):
        self.kwargs.update({
            'loc': 'northeurope',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='servicebus-nscli', length=20),
            'namespacename1': self.create_random_name(prefix='servicebus-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='servicebus-nscli', length=20),
            'namespacename3': self.create_random_name(prefix='servicebus-nscli', length=20),
            'namespacename5': self.create_random_name(prefix='servicebus-nscli', length=20),
            'namespacename6': self.create_random_name(prefix='servicebus-nscli', length=20),
            'identity1': self.create_random_name(prefix='sb-identity1', length=20),
            'identity2': self.create_random_name(prefix='sb-identity2', length=20),
            'identity3': self.create_random_name(prefix='sb-identity3', length=20),
            'identity4': self.create_random_name(prefix='sb-identity4', length=20),
            'sku': 'Premium',
            'tier': 'Premium',
            'system': 'SystemAssigned',
            'user': 'UserAssigned',
            'systemuser': 'SystemAssigned, UserAssigned',
            'none': 'None'
        })

        identity1 = self.cmd('identity create --name {identity1} --resource-group {rg}').get_output_in_json()
        self.assertEqual(identity1['name'], self.kwargs['identity1'])
        self.kwargs.update({'id1':identity1['id']})

        identity2 = self.cmd('identity create --name {identity2} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id2': identity2['id']})

        identity3 = self.cmd('identity create --name {identity3} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id3': identity3['id']})

        identity4 = self.cmd('identity create --name {identity4} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id4': identity4['id']})

        # Check for the NameSpace name Availability
        #self.cmd('eventhubs namespace exists --name {namespacename}', checks=[self.check('nameAvailable', True)])

        namespace = self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename1} --location {loc} --sku {sku} --mi-user-assigned {id1} {id2} {id3}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['user'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 3

        namespace = self.cmd(
            'servicebus namespace identity remove --resource-group {rg} --name {namespacename1} --user-assigned {id1} {id2}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['user'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 1

        namespace = self.cmd(
            'servicebus namespace identity assign --resource-group {rg} --name {namespacename1} --user-assigned {id1} {id2}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['user'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 3

        namespace = self.cmd(
            'servicebus namespace identity assign --resource-group {rg} --name {namespacename1} --system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 3

        namespace = self.cmd(
            'servicebus namespace identity remove --resource-group {rg} --name {namespacename1} --user-assigned {id1} {id2} {id3}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['system'])

        #0.1
        namespace = self.cmd('servicebus namespace create --resource-group {rg} --name {namespacename} --location {loc} --sku {sku} --mi-system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['system'])

        #5
        namespace = self.cmd('servicebus namespace identity remove --resource-group {rg} --namespace-name {namespacename} --system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity'], None)

        #1
        namespace = self.cmd('servicebus namespace identity assign --resource-group {rg} --namespace-name {namespacename} --system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['system'])

        #2
        namespace = self.cmd('servicebus namespace identity assign --resource-group {rg} --namespace-name {namespacename} --user-assigned {id1} {id2}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2

        #9
        namespace = self.cmd('servicebus namespace identity remove --resource-group {rg} --namespace-name {namespacename} --system-assigned --user-assigned {id1} {id2}').get_output_in_json()
        self.assertEqual(namespace['identity'], None)

        #3
        namespace = self.cmd('servicebus namespace identity assign --resource-group {rg} --namespace-name {namespacename} --user-assigned {id1} {id2} {id3}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['user'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 3

        #4
        namespace = self.cmd('servicebus namespace identity assign --resource-group {rg} --namespace-name {namespacename} --system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 3

        #8
        namespace = self.cmd('servicebus namespace identity remove --resource-group {rg} --namespace-name {namespacename} --user-assigned {id1} {id2} {id3}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['system'])

        #2
        namespace = self.cmd('servicebus namespace identity assign --resource-group {rg} --namespace-name {namespacename} --user-assigned {id1}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 1

        #6
        namespace = self.cmd('servicebus namespace identity remove --resource-group {rg} --namespace-name {namespacename} --system-assigned').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['user'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 1

        #7
        namespace = self.cmd('servicebus namespace identity remove --resource-group {rg} --namespace-name {namespacename} --user-assigned {id1}').get_output_in_json()
        self.assertEqual(namespace['identity'], None)

        # Create Namespace
        #self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename1} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits} --cluster-arm-id {clusterarmid}')

        # Get Created Namespace
        #principal_id = self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}').get_output_in_json().get("identity").get("principalId")

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename1}')
