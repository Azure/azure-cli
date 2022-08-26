# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimDeletedServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_apim_deleted_service-')
    @ApiManagementPreparer(sku_name='Consumption', parameter_name='apim_name', parameter_name_for_location='apim_location')
    def test_apim_deleted_service(self, apim_location, apim_name):
        self.kwargs.update({'apim_location': apim_location})

        self._delete()
        self._list(apim_name)
        self._show()
        self._purge(apim_name)

    def _delete(self):
        self.cmd('apim delete -g {rg} -n {apim} -y', checks=[self.is_empty()])

    def _list(self, apim_name):
        self._assert_soft_deleted(apim_name, True)

    def _show(self):
        self.cmd('apim deleted-service show -l {apim_location} -n {apim}',
                    checks=[
                        self.check('name', '{apim}'),
                        self.check('type', 'Microsoft.ApiManagement/deletedservices')])

    def _purge(self, apim_name):
        self.cmd('apim deleted-service purge -l {apim_location} -n {apim}')
        self._assert_soft_deleted(apim_name, False) # should no longer be in the list

    def _assert_soft_deleted(self, apim_name, assertion=True):
        output = self.cmd('apim deleted-service list').get_output_in_json()
        result = any(item['name'] == apim_name for item in output)
        self.assertEqual(assertion, result)
