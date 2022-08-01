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
        signalr_name = self.create_random_name('signalr', 16)
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
            'kv_secret': 'azureclitest',
            'identity': '/subscriptions/9caf2a1e-9c49-49b6-89a2-56bdec7e3f97/resourcegroups/azureclitest/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azureclitestmsi',
            'custom_cert_name': 'test-cert'
        })

        signalr = self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku}  -l {location}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}')
        ]).get_output_in_json()

        self.cmd('az signalr identity assign --identity {identity} -n {signalr_name} -g {rg}')

        self.cmd('az signalr custom-certificate create -g {rg} --signalr-name {signalr_name} --keyvault-base-uri {kv_base_uri} --keyvault-secret-name {kv_secret} --name {custom_cert_name}')




