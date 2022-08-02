# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only


class AzureSignalRServiceCustomDomainScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_private_endpoint(self, resource_group):
        signalr_name = 'signalrcliteststatic'
        sku = 'Premium_P1'
        unit_count = 1
        location = 'eastus'

        self.kwargs.update({
            'location': location,
            'signalr_name': signalr_name,
            'sku': sku,
            'unit_count': unit_count,
            'kv_base_uri': 'https://azureclitestkv.vault.azure.net/',
            'kv_group': 'azureclitest',
            'kv_name': 'azureclitestkv',
            'kv_s_name': 'azureclitest',
            'identity': '/subscriptions/9caf2a1e-9c49-49b6-89a2-56bdec7e3f97/resourcegroups/azureclitest/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azureclitestmsi',
            'custom_cert_name': 'test-cert',
            'custom_domain_resource_name': 'test-domain',
            'custom_domain_name': 'clitest.manual-test.dev.signalr.azure.com'
        })

        self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku}  -l {location}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}')
        ])

        self.cmd('az signalr identity assign --identity {identity} -n {signalr_name} -g {rg}')

        self.cmd('az signalr custom-certificate create -g {rg} --signalr-name {signalr_name} --keyvault-base-uri {kv_base_uri} --keyvault-secret-name {kv_s_name} --name {custom_cert_name}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        cert = self.cmd('az signalr custom-certificate show -g {rg} --signalr-name {signalr_name} --name {custom_cert_name}', checks=[
            self.check('name', '{custom_cert_name}'),
            self.check('keyVaultBaseUri', '{kv_base_uri}'),
            self.check('keyVaultSecretName', '{kv_s_name}'),
            self.check('provisioningState', 'Succeeded'),
        ]).get_output_in_json()

        self.kwargs.update({'cert_resource_id': cert['id']})

        self.cmd('az signalr custom-certificate list -g {rg} --signalr-name {signalr_name}', checks=[
            self.check('[0].name', '{custom_cert_name}'),
            self.check('[0].keyVaultBaseUri', '{kv_base_uri}'),
            self.check('[0].keyVaultSecretName', '{kv_s_name}'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az signalr custom-domain create -g {rg} --signalr-name {signalr_name} --name {custom_domain_resource_name} --domain-name {custom_domain_name} --certificate-resource-id {cert_resource_id}', checks=[
            self.check('domainName', '{custom_domain_name}'),
        ])

        self.cmd('az signalr custom-domain show -g {rg} --signalr-name {signalr_name} --name {custom_domain_resource_name}', checks=[
            self.check('domainName', '{custom_domain_name}'),
            self.check('name', '{custom_domain_resource_name}'),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az signalr custom-domain list -g {rg} --signalr-name {signalr_name}', checks=[
            self.check('[0].domainName', '{custom_domain_name}'),
            self.check('[0].name', '{custom_domain_resource_name}'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az signalr delete -g {rg} -n {signalr_name}')





