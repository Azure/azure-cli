# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.command_modules.appconfig.tests.latest._test_utils import _create_config_store, CredentialResponseSanitizer

class AppConfigIdentityScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_identity(self, resource_group, location):

        config_store_name = self.create_random_name(prefix='IdentityTest', length=24)

        location = 'eastus'
        sku = 'standard'
        identity_name = self.create_random_name(prefix='UserAssignedIdentity', length=24)

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'identity_name': identity_name
        })

        _create_config_store(self, self.kwargs)
        user_assigned_identity = _create_user_assigned_identity(self, self.kwargs)

        self.kwargs.update({
            'identity_id': user_assigned_identity['id']
        })

        self.cmd('appconfig identity assign -n {config_store_name} -g {rg}',
                 checks=[self.check('type', 'SystemAssigned'),
                         self.check('userAssignedIdentities', None)])

        self.cmd('appconfig identity assign -n {config_store_name} -g {rg} --identities {identity_id}',
                 checks=[self.check('type', 'SystemAssigned, UserAssigned')])

        self.cmd('appconfig identity remove -n {config_store_name} -g {rg} --identities {identity_id}')

        self.cmd('appconfig identity show -n {config_store_name} -g {rg}',
                 checks=[self.check('type', 'SystemAssigned'),
                         self.check('userAssignedIdentities', None)])


def _create_user_assigned_identity(test, kwargs):
    return test.cmd('identity create -n {identity_name} -g {rg}').get_output_in_json()
