# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNamespaceMSITesting(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_sb_namespace_encryption(self, resource_group):
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
            'none': 'None',
            'key1': 'key1',
            'key2': 'key2',
            'key3': 'key3',
            'key4': 'key4',
            'key5': 'key5',
            'kv_name': self.create_random_name(prefix='eventhubs-kv', length=20)
        })

        identity1 = self.cmd('identity create --name {identity1} '+
                             '--resource-group {rg}').get_output_in_json()
        self.assertEqual(identity1['name'], self.kwargs['identity1'])
        self.kwargs.update({'id1':identity1['id']})

        identity2 = self.cmd('identity create --name {identity2} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id2': identity2['id']})

        identity3 = self.cmd('identity create --name {identity3} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id3': identity3['id']})

        identity4 = self.cmd('identity create --name {identity4} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id4': identity4['id']})

        keyvaultcreate = self.cmd('keyvault create --resource-group {rg} --name {kv_name} --location {loc} --enable-soft-delete --enable-purge-protection').get_output_in_json()

        self.kwargs.update({
            'id1object': identity1['principalId'],
            'id2object': identity2['principalId'],
            'id3object': identity3['principalId'],
            'id4object': identity4['principalId'],
            'key_uri': keyvaultcreate['properties']['vaultUri']
        })


        self.cmd(
            'keyvault set-policy -n {kv_name} -g {rg} --object-id {id1object} --key-permissions  all')
        self.cmd(
            'keyvault set-policy -n {kv_name} -g {rg} --object-id {id2object} --key-permissions  all')
        self.cmd(
            'keyvault set-policy -n {kv_name} -g {rg} --object-id {id3object} --key-permissions  all')
        self.cmd(
            'keyvault set-policy -n {kv_name} -g {rg} --object-id {id3object} --key-permissions  all')
        self.cmd('keyvault key create -n {key1} --vault-name {kv_name}')
        self.cmd('keyvault key create -n {key2} --vault-name {kv_name}')
        self.cmd('keyvault key create -n {key3} --vault-name {kv_name}')

        namespace = self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename1} --sku {sku} --location {loc} --mi-system-assigned'
        ).get_output_in_json()

        self.kwargs.update({'pId': namespace['identity']['principalId']})

        self.cmd(
            'keyvault set-policy -n {kv_name} -g {rg} --object-id {pId} --key-permissions  all')

        namespace = self.cmd(
            'servicebus namespace encryption add --resource-group {rg} --namespace-name {namespacename1}' +
            ' --encryption-config key-name={key1} key-vault-uri={key_uri}'
            ' --encryption-config key-name={key2} key-vault-uri={key_uri}').get_output_in_json()
        self.assertEqual(namespace['identity']['type'], self.kwargs['system'])
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 2


        namespace = self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --sku {sku} --location {loc} --mi-system-assigned --mi-user-assigned {id1} {id2}' +
            ' --encryption-config key-name={key1} key-vault-uri={key_uri} user-assigned-identity={id1}' +
            ' --encryption-config key-name={key2} key-vault-uri={key_uri} user-assigned-identity={id1}' +
            ' --encryption-config key-name={key3} key-vault-uri={key_uri} user-assigned-identity={id1}'
        ).get_output_in_json()

        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 3

        namespace = self.cmd('servicebus namespace encryption remove --resource-group {rg} --namespace-name {namespacename}' +
                             ' --encryption-config key-name={key1} key-vault-uri={key_uri} user-assigned-identity={id1}').get_output_in_json()

        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 2

        namespace = self.cmd('servicebus namespace encryption add --resource-group {rg} --namespace-name {namespacename}' +
                             ' --encryption-config key-name={key1} key-vault-uri={key_uri} user-assigned-identity={id1}').get_output_in_json()

        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 3

        namespace = self.cmd('servicebus namespace encryption remove --resource-group {rg} --namespace-name {namespacename}' +
                             ' --encryption-config key-name={key2} key-vault-uri={key_uri} user-assigned-identity={id1}' +
                             ' --encryption-config key-name={key3} key-vault-uri={key_uri} user-assigned-identity={id1}').get_output_in_json()

        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 1

        namespace = self.cmd('servicebus namespace encryption add --resource-group {rg} --namespace-name {namespacename}' +
                             ' --encryption-config key-name={key2} key-vault-uri={key_uri} user-assigned-identity={id1}' +
                             ' --encryption-config key-name={key3} key-vault-uri={key_uri} user-assigned-identity={id1}').get_output_in_json()

        self.assertEqual(namespace['identity']['type'], self.kwargs['systemuser'])
        n = [i for i in namespace['identity']['userAssignedIdentities']]
        assert len(n) == 2
        n = [i for i in namespace['encryption']['keyVaultProperties']]
        assert len(n) == 3



