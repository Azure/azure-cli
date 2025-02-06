# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import _create_config_store, CredentialResponseSanitizer

class AppConfigCredentialScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_credential(self, resource_group, location):

        config_store_name = self.create_random_name(prefix='CredentialTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })

        _create_config_store(self, self.kwargs)

        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        assert len(credential_list) == 4
        assert next(credential['connectionString']
                    for credential in credential_list if not credential['readOnly'])

        self.kwargs.update({
            'id': credential_list[0]['id']
        })

        self.cmd('appconfig credential regenerate -n {config_store_name} -g {rg} --id {id}',
                 checks=[self.check('name', credential_list[0]['name'])])
