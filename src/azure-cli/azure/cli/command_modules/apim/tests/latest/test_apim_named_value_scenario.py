# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimNamedValueScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_apim_nv-')
    @ApiManagementPreparer(sku_name='Consumption')
    def test_apim_named_value(self):
        self._create_named_value()._then_get_named_value()
        self._create_named_value_secret()._then_get_named_value_secret()
        self._update_named_value()
        self._list_named_values()
        self._delete_named_value()

    def _delete_named_value(self):
        self.cmd('apim named-value delete -g {rg} --service-name {apim} --id {nv_id} -y')
        count = len(self.cmd('apim named-value list -g {rg} --service-name {apim}').get_output_in_json())
        self.assertEqual(count, 1)

    def _update_named_value(self):
        self.kwargs.update({
            'updated_value': self.create_random_name('updated-value', 24),
        })
        self.cmd('apim named-value update -g "{rg}" -n "{apim}" --id "{nv_id}" --value "{updated_value}"')

    def _create_named_value(self):
        self.kwargs.update({
            'display_name': self.create_random_name('nv-name', 14),
            'value': 'testvalue123',
            'nv_id': self.create_random_name('az-nv', 12),
            'tags': "foo=baz"
        })
        self.cmd('apim named-value create -g {rg} -n {apim} --display-name "{display_name}" --value "{value}" --id "{nv_id}" --secret false --tags "{tags}"', checks=[
            self.check('displayName', '{display_name}'),
            self.check('secret', False)
        ])
        return self

    def _list_named_values(self):
        count = len(self.cmd('apim named-value list -g {rg} -n {apim}').get_output_in_json())
        self.assertEqual(count, 2)

    def _create_named_value_secret(self):
        self.kwargs.update({
            'secret_display_name': self.create_random_name('nv-sec', 10),
            'secret_value': 'secrettestvalue123',
            'secret_nv_id': self.create_random_name('az-nv-sec', 25),
            'secret_tags': "secret=true"
        })
        self.cmd('apim named-value create -g "{rg}" -n "{apim}" --display-name "{secret_display_name}" --value "{secret_value}" --id "{secret_nv_id}" --secret true --tags "{secret_tags}"', checks=[
            self.check('displayName', '{secret_display_name}'),
            self.check('secret', True)
        ])
        return self

    def _then_get_named_value(self):
        self.cmd('apim named-value show -g "{rg}" -n "{apim}" --id "{nv_id}" --secret false', checks=[
            self.check('value', '{value}')
        ])

    def _then_get_named_value_secret(self):
        self.cmd('apim named-value show -g "{rg}" -n "{apim}" --id {secret_nv_id} --secret true', checks=[
            self.check('value', '{secret_value}')
        ])
