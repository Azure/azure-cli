# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServiceUpstreamScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_upstream(self, resource_group):
        signalr_name = self.create_random_name('signalr', 16)
        sku = 'Standard_S1'
        unit_count = 1
        location = 'eastus'
        tags_key = 'key'
        tags_val = 'value'
        service_mode = 'Classic'
        allowed_origins = ['http://example1.com', 'http://example2.com']
        updated_sku = 'Free_F1'
        updated_tags_val = 'value2'
        update_service_mode = 'Serverless'
        added_allowed_origins = ['http://example3.com', 'http://example4.com']

        self.kwargs.update({
            'location': location,
            'signalr_name': signalr_name,
            'sku': sku,
            'unit_count': unit_count,
            'tags': '{}={}'.format(tags_key, tags_val),
            'service_mode': service_mode,
            'allowed_origins': ' '.join(allowed_origins),
            'updated_sku': updated_sku,
            'updated_tags': '{}={}'.format(tags_key, updated_tags_val),
            'update_service_mode': update_service_mode,
            'added_allowed_origins': ' '.join(added_allowed_origins),
            'default_action': "Deny",
            'url_template_1': 'http://host1.com',
            'url_template_2': 'http://host2.com',
            'hub_pattern_1': 'chat',
            'hub_pattern_2': '*',
            'category_pattern_1': 'connections',
            'category_pattern_2': 'messages',
            'event_pattern_1': 'connected',
            'event_pattern_2': '*',
        })

        # Test create
        self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku} --unit-count {unit_count} -l {location} --tags {tags} --service-mode {service_mode} --allowed-origins {allowed_origins} --default-action {default_action}',
                 checks=[
                     self.check('name', '{signalr_name}'),
                     self.check('location', '{location}'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('sku.name', '{sku}'),
                     self.check('sku.capacity', '{unit_count}'),
                     self.check('tags.{}'.format(tags_key), tags_val),
                     self.check('features[0].value', '{service_mode}'),
                     self.check('cors.allowedOrigins', allowed_origins),
                     self.exists('hostName'),
                     self.exists('publicPort'),
                     self.exists('serverPort'),
                     self.check('networkAcLs.defaultAction', '{default_action}')
                 ])

        # Test upstream update
        self.cmd('az signalr upstream update -n {signalr_name} -g {rg} --template url-template="{url_template_1}" category-pattern="{category_pattern_1}" hub-pattern={hub_pattern_1} event-pattern={event_pattern_1} --template url-template={url_template_2} category-pattern={category_pattern_2}', checks=[
            self.check('upstream.templates[0].urlTemplate', '{url_template_1}'),
            self.check('upstream.templates[0].hubPattern', '{hub_pattern_1}'),
            self.check('upstream.templates[0].categoryPattern', '{category_pattern_1}'),
            self.check('upstream.templates[0].eventPattern', '{event_pattern_1}'),
            self.check('upstream.templates[1].urlTemplate', '{url_template_2}'),
            self.check('upstream.templates[1].hubPattern', '{hub_pattern_2}'),
            self.check('upstream.templates[1].categoryPattern', '{category_pattern_2}'),
            self.check('upstream.templates[1].eventPattern', '{event_pattern_2}')
        ])

        # Test upstream list
        self.cmd('az signalr upstream list -n {signalr_name} -g {rg}', checks=[
            self.check('templates[0].urlTemplate', '{url_template_1}'),
            self.check('templates[0].hubPattern', '{hub_pattern_1}'),
            self.check('templates[0].categoryPattern', '{category_pattern_1}'),
            self.check('templates[0].eventPattern', '{event_pattern_1}'),
            self.check('templates[1].urlTemplate', '{url_template_2}'),
            self.check('templates[1].hubPattern', '{hub_pattern_2}'),
            self.check('templates[1].categoryPattern', '{category_pattern_2}'),
            self.check('templates[1].eventPattern', '{event_pattern_2}')
        ])

        # Test upstream clear
        self.cmd('az signalr upstream clear -n {signalr_name} -g {rg}', checks=[
            self.check('length(upstream.templates)', 0)
        ])
