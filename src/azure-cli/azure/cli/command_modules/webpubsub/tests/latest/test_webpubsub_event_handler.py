# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from .recording_processors import KeyReplacer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class WebpubsubEventHandlerTest(ScenarioTest):

    def __init__(self, method_name):
        super(WebpubsubEventHandlerTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    @ResourceGroupPreparer(random_name_length=20)
    def test_webpubsub_event_handler(self, resource_group):
        tags_key = 'key'
        tags_val = 'value'
        updated_tags_val = 'value2'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'name': self.create_random_name('webpubsub', 16),
            'sku': 'Standard_S1',
            'location': 'eastus',
            'tags': '{}={}'.format(tags_key, tags_val),
            'unit_count': 1,
            'updated_tags': '{}={}'.format(tags_key, updated_tags_val),
            'updated_sku': 'Free_F1',
            'hub': 'myHub',
            'urlTemplate1': 'http://host.com',
            'userEventPattern1': 'event1,event2',
            'systemEventPattern1': 'connect',
            'urlTemplate2': 'http://host2.com',
            'userEventPattern2': 'event3,event4',
            'systemEventPattern2': 'disconnect,connected',
            'params': os.path.join(curr_dir, 'parameter.json').replace('\\', '\\\\'),
        })

        # Create
        self.cmd('webpubsub create -g {rg} -n {name} --tags {tags} -l {location} --sku {sku} --unit-count {unit_count}', checks=[
            self.check('name', '{name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', '{unit_count}'),
            self.check('tags.{}'.format(tags_key), tags_val),
            self.exists('hostName'),
            self.exists('publicPort'),
            self.exists('serverPort'),
            self.exists('externalIp'),
            self.exists('eventHandler')
        ])

        # Test event handler update
        self.cmd('webpubsub event-handler update -g {rg} -n {name} --items @"{params}"', checks=[
            self.check('eventHandler.items.{hub}[0].urlTemplate', '{urlTemplate1}'),
            self.check('eventHandler.items.{hub}[0].userEventPattern', '{userEventPattern1}'),
            self.check('eventHandler.items.{hub}[0].systemEventPattern', '{systemEventPattern1}'),
        ])

        # Test event handler hub remove
        self.cmd('webpubsub event-handler hub remove  -g {rg} -n {name} --hub-name {hub}', checks=[
            self.check('length(eventHandler.items)', 0)
        ])

        # Test event handler hub update
        self.cmd('webpubsub event-handler hub update -g {rg} -n {name} --hub-name {hub} --template url-template={urlTemplate2} user-event-pattern={userEventPattern2} system-event-pattern={systemEventPattern2}', checks=[
            self.check('eventHandler.items.{hub}[0].urlTemplate', '{urlTemplate2}'),
            self.check('eventHandler.items.{hub}[0].userEventPattern', '{userEventPattern2}'),
            self.check('eventHandler.items.{hub}[0].systemEventPattern', '{systemEventPattern2}'),
        ])

        # Test delete
        count = len(self.cmd('webpubsub list').get_output_in_json())
        self.cmd('webpubsub delete -g {rg} -n {name}')
        final_count = len(self.cmd('webpubsub list').get_output_in_json())
        self.assertTrue(final_count == count - 1)
