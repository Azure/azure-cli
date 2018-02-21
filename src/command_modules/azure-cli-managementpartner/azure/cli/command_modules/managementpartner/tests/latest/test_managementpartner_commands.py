# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk import ScenarioTest, record_only


@record_only()
class AzureManagementPartnerTests(ScenarioTest):

    def _validate_managementpartner(self, partner):
        self.assertIsNotNone(partner)
        self.assertTrue(partner['objectId'])
        self.assertTrue(partner['partnerId'])
        self.assertTrue(partner['state'])
        self.assertTrue(partner['tenantId'])

    def test_delete_managementpartner(self):
        self.kwargs.update({
            'partnerid': '123456'
        })

        # Setup
        self.cmd('az managementpartner create --partner-id {partnerid}')

        # Run
        self.cmd('az managementpartner delete --partner-id {partnerid}')

    def test_create_managementpartner(self):
        self.kwargs.update({
            'partnerid': '123456'
        })
        # Run
        result = self.cmd('az managementpartner create --partner-id {partnerid}') \
                     .get_output_in_json()
        # Validate
        self._validate_managementpartner(result)

        # Cleanup
        self.cmd('az managementpartner delete --partner-id {partnerid}')

    def test_show_managementpartner(self):
        self.kwargs.update({
            'partnerid': '123456'
        })
        # Setup
        self.cmd('az managementpartner create --partner-id {partnerid}')

        # Run
        result = self.cmd('az managementpartner show --partner-id {partnerid}')\
                     .get_output_in_json()

        # Validate
        self._validate_managementpartner(result)

        # Cleanup
        self.cmd('az managementpartner delete --partner-id {partnerid}')

    def test_update_managementpartner(self):
        self.kwargs.update({
            'partnerid': '123456',
            'newpartnerid': '123457'
        })
        # Setup
        self.cmd('az managementpartner create --partner-id {partnerid}')

        # Run
        result = self.cmd('az managementpartner update --partner-id {newpartnerid}')\
                     .get_output_in_json()

        # Validate
        self._validate_managementpartner(result)

        # Cleanup
        self.cmd('az managementpartner delete --partner-id {newpartnerid}')
