# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServiceReplicaTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_replica(self, resource_group):
        signalr_name = self.create_random_name('signalr', 16)
        sku = 'Premium_P1'
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
        replica_name = 'clitestReplica'
        replica_location = 'westus'

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
            'replica_name': replica_name,
            'replica_location': replica_location,
        })

        # Test primary create
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

        # test create replica
        self.cmd('az signalr replica create --signalr-name {signalr_name} --replica-name {replica_name} -g {rg} --sku {sku} --unit-count {unit_count} -l {replica_location} --tags {tags}', checks=[
            self.check('name', '{replica_name}'),
            self.check('location', '{replica_location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('tags.{}'.format(tags_key), tags_val),
        ])

        # test show replica
        self.cmd('az signalr replica show --signalr-name {signalr_name} --replica-name {replica_name} -g {rg}', checks=[
            self.check('name', '{replica_name}'),
            self.check('location', '{replica_location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('tags.{}'.format(tags_key), tags_val),
        ])

        # test list replica
        self.cmd('az signalr replica list --signalr-name {signalr_name} -g {rg}', checks=[
            self.check('[0].name', '{replica_name}'),
            self.check('[0].location', '{replica_location}'),
            self.check('[0].provisioningState', 'Succeeded'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].tags.{}'.format(tags_key), tags_val),
        ])

        # test remove replica
        count = len(self.cmd('az signalr replica list --signalr-name {signalr_name} -g {rg}').get_output_in_json())
        self.cmd('az signalr replica delete --signalr-name {signalr_name} --replica-name {replica_name} -g {rg}')
        final_count = len(
            self.cmd('az signalr replica list --signalr-name {signalr_name} -g {rg}').get_output_in_json())
        self.assertTrue(final_count == count - 1)
