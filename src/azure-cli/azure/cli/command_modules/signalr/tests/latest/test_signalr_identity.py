# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServiceIdentityTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_identity(self, resource_group):
        signalr_name = self.create_random_name('signalr', 16)
        sku = 'Standard_S1'
        unit_count = 1
        location = 'eastus'
        tags_key = 'key'
        tags_val = 'value'
        service_mode = 'Classic'
        enable_message_logs_input = 'true'
        enable_message_logs_check = True
        allowed_origins = ['http://example1.com', 'http://example2.com']
        updated_sku = 'Free_F1'
        updated_tags_val = 'value2'
        update_service_mode = 'Serverless'
        update_enable_message_logs_input = 'false'
        update_enable_message_logs_check = False
        added_allowed_origins = ['http://example3.com', 'http://example4.com']

        self.kwargs.update({
            'location': location,
            'signalr_name': signalr_name,
            'sku': sku,
            'unit_count': unit_count,
            'tags': '{}={}'.format(tags_key, tags_val),
            'enable_message_logs_input': enable_message_logs_input,
            'enable_message_logs_check': enable_message_logs_check,
            'service_mode': service_mode,
            'allowed_origins': ' '.join(allowed_origins),
            'updated_sku': updated_sku,
            'updated_tags': '{}={}'.format(tags_key, updated_tags_val),
            'update_service_mode': update_service_mode,
            'update_enable_message_logs_input': update_enable_message_logs_input,
            'update_enable_message_logs_check': update_enable_message_logs_check,
            'added_allowed_origins': ' '.join(added_allowed_origins),
            'default_action': "Deny",
        })

        # create
        self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku} --unit-count {unit_count} -l {location}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}')
        ])

        # assign identity
        self.cmd('az signalr identity assign -n {signalr_name} -g {rg} --identity [system]', checks=[
            self.check('identity.type', 'SystemAssigned'),
        ])

        # test show identity
        self.cmd('az signalr identity show -n {signalr_name} -g {rg}', checks=[
            self.check('type', 'SystemAssigned'),
        ])

        # test remove
        self.cmd('az signalr identity remove -n {signalr_name} -g {rg}', checks=[
            self.check('identity', None),
        ])
