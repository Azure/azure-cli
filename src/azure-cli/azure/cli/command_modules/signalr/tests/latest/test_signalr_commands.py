# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_commands(self, resource_group):
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

        # Test create
        self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku} --unit-count {unit_count} -l {location} --tags {tags} --service-mode {service_mode} --enable-message-logs {enable_message_logs_input} --allowed-origins {allowed_origins} --default-action {default_action}',
                 checks=[
                     self.check('name', '{signalr_name}'),
                     self.check('location', '{location}'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('sku.name', '{sku}'),
                     self.check('sku.capacity', '{unit_count}'),
                     self.check('tags.{}'.format(tags_key), tags_val),
                     self.check('features[0].value', '{service_mode}'),
                     self.check('features[2].value', '{enable_message_logs_check}'),
                     self.check('cors.allowedOrigins', allowed_origins),
                     self.exists('hostName'),
                     self.exists('publicPort'),
                     self.exists('serverPort'),
                     self.check('networkAcLs.defaultAction', '{default_action}')
                 ])

        # Test show
        self.cmd('az signalr show -n {signalr_name} -g {rg}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', '{unit_count}'),
            self.check('features[0].value', '{service_mode}'),
            self.check('features[2].value', '{enable_message_logs_check}'),
            self.check('cors.allowedOrigins', allowed_origins),
            self.exists('hostName'),
            self.exists('publicPort'),
            self.exists('serverPort'),
            self.exists('externalIp'),
            self.check('networkAcLs.defaultAction', '{default_action}')
        ])

        # Test list
        self.cmd('az signalr list -g {rg}', checks=[
            self.check('[0].name', '{signalr_name}'),
            self.check('[0].location', '{location}'),
            self.check('[0].provisioningState', 'Succeeded'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].sku.capacity', '{unit_count}'),
            self.check('[0].features[0].value', '{service_mode}'),
            self.check('[0].features[2].value', '{enable_message_logs_check}'),
            self.check('[0].cors.allowedOrigins', allowed_origins),
            self.exists('[0].hostName'),
            self.exists('[0].publicPort'),
            self.exists('[0].serverPort'),
            self.exists('[0].externalIp'),
            self.check('[0].networkAcLs.defaultAction', '{default_action}')
        ])

        # Test update
        self.cmd('az signalr update -n {signalr_name} -g {rg} --sku {updated_sku} --tags {updated_tags} --service-mode {update_service_mode} --enable-message-logs {update_enable_message_logs_input}',
                 checks=[
                     self.check('name', '{signalr_name}'),
                     self.check('location', '{location}'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('sku.name', '{updated_sku}'),
                     self.check('tags.{}'.format(tags_key), updated_tags_val),
                     self.check('features[0].value', '{update_service_mode}'),
                     self.check('features[2].value', '{update_enable_message_logs_check}'),
                     self.check('cors.allowedOrigins', allowed_origins),
                     self.exists('hostName'),
                     self.exists('publicPort'),
                     self.exists('serverPort')
                 ])

        # Test CORS operations
        self.cmd('az signalr cors remove -n {signalr_name} -g {rg} --allowed-origins {allowed_origins}', checks=[
            self.check('cors.allowedOrigins[0]', '*')
        ])

        self.cmd('az signalr cors add -n {signalr_name} -g {rg} --allowed-origins {added_allowed_origins}', checks=[
            self.check('cors.allowedOrigins', ['*'] + added_allowed_origins)
        ])

        self.cmd('az signalr cors update -n {signalr_name} -g {rg} --allowed-origins {added_allowed_origins}', checks=[
            self.check('cors.allowedOrigins', added_allowed_origins)
        ])

        # Test key list
        self.cmd('az signalr key list -n {signalr_name} -g {rg}', checks=[
            self.exists('primaryKey'),
            self.exists('secondaryKey')
        ])

        # Test key renew
        self.cmd('az signalr key renew -n {signalr_name} -g {rg} --key-type secondary', checks=[
            self.exists('primaryKey'),
            self.exists('secondaryKey')
        ])
