# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimSubscriptionScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimSubscriptionScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name', sku_name='Consumption')
    def test_apim_subscription(self, resource_group, apim_name):
        # setup
        self.kwargs.update({'apim_name': apim_name})
        self._set_subscription_count(self._get_subscription_count())

        # act out scenarios
        self._create_subscription()
        self._show_subscription()
        self._update_subscription()
        self._regenerate_keys()
        self._delete_subscription()

    def _create_subscription(self):
        self.cmd('apim subscription create -n {apim_name} -g {rg} --sid {subscription_id} --scope {scope} -d {display_name}', checks=[
            self.check('name', '{subscription_id}')
        ])

    def _show_subscription(self):
        self.subscription = self.cmd('apim subscription show -n {apim_name} -g {rg} --sid {subscription_id}').get_output_in_json()

    def _update_subscription(self):
        updated_subscription = self.cmd('apim subscription update -n {apim_name} -g {rg} --sid {subscription_id} -d {updated_display_name}').get_output_in_json()
        assert updated_subscription['displayName'] != self.subscription['displayName']

    def _regenerate_keys(self):
        original_keys = self.cmd('apim subscription keys list -n {apim_name} -g {rg} --sid {subscription_id}').get_output_in_json()
        self.cmd('apim subscription keys regenerate --key-kind primary -n {apim_name} -g {rg} --sid {subscription_id}')
        self.cmd('apim subscription keys regenerate --key-kind secondary -n {apim_name} -g {rg} --sid {subscription_id}')
        modified_keys = self.cmd('apim subscription keys list -n {apim_name} -g {rg} --sid {subscription_id}').get_output_in_json()

        assert original_keys['primaryKey'] != modified_keys['primaryKey']
        assert original_keys['secondaryKey'] != modified_keys['secondaryKey']

    def _delete_subscription(self):
        self.cmd('apim subscription delete -n {apim_name} -g {rg} --sid {subscription_id} --yes')
        self.assertLessEqual(self._get_subscription_count(), 1)

    def _set_subscription_count(self, value):
        self.subscription_count = value

    def _get_subscription_count(self):
        return len(self.cmd('apim subscription list -n {apim_name} -g {rg}').get_output_in_json())

    def _initialize_variables(self):
        self.subscription_id = self.create_random_name('apim_subscription-', 50)
        self.display_name = 'foo-bar'
        self.updated_display_name = 'bar-foo'
        self.state = 'Submitted'
        self.primary_key = 'd370c19509d24781a5a6d6cf15604e52'
        self.secondary_key = 'd370c19509d24781a5a6d6cf15604e52'
        self.allow_tracing = True
        self.scope = "/apis"

        self.kwargs.update({
            'subscription_id': self.subscription_id,
            'display_name': self.display_name,
            'state': self.state,
            'primary_key': self.primary_key,
            'secondary_key': self.secondary_key,
            'allow_tracing': self.allow_tracing,
            'scope': self.scope,
            'updated_display_name': self.updated_display_name
        })
