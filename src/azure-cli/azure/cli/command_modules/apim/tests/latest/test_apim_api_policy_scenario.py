# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import xmltodict
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimApiPolicyScenarioTest(ScenarioTest):
    API_ID = 'echo-api'

    def setUp(self):
        self.data = self.XmlPolicyData()
        self.data.create_xml_file()
        super(ApimApiPolicyScenarioTest, self).setUp()

    def tearDown(self):
        self.data.delete_xml_file()
        super(ApimApiPolicyScenarioTest, self).tearDown()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name')
    def test_apim_api_policy(self, resource_group, apim_name):
        self.kwargs.update({
            'apim_name': apim_name,
            'api_id': self.API_ID,
            'xml_value': self.data.xml_content,
            'xml_file': self.data.policy_file
        })

        self._create_policy_using_inline_xml()
        self._create_policy_using_xml_from_file()

    def _create_policy_using_inline_xml(self):
        self._assert_xml_output_is_equal_to_expected('apim api policy create -n {apim_name} -g {rg} -a {api_id} -v "{xml_value}" --output tsv --query value')

    def _create_policy_using_xml_from_file(self):
        self._assert_xml_output_is_equal_to_expected('apim api policy create -n {apim_name} -g {rg} -a {api_id} -f {xml_file} --output tsv --query value')

    def _assert_xml_output_is_equal_to_expected(self, cmd_statement):
        result = xmltodict.parse(self.cmd(cmd_statement).output)
        expected = xmltodict.parse(self.data.xml_content)

        self.assertDictEqual(expected, result)

    def _delete_policy_removes_the_policy_resource(self):
        self.cmd('apim api policy delete -n {apim_name} -g {rg} -a {api_id}')
        final_count = self.cmd('apim api policy list -n {apim_name} -g {rg} -a {api_id}').get_output_in_json()['count']

        self.assertEqual(0, final_count)  # 0 used here since the default APIM products were deleted

    class XmlPolicyData:
        """Test XML Policy data management for the scenario test"""
        POLICY_FILE_NAME = 'data/api_policy.xml'

        xml_content = """<policies>
        <inbound></inbound>
        <backend>
                <!-- test -->
        </backend>
        <outbound />
        <on-error />
</policies>"""

        xml_update_content = """<policies>
        <inbound>
        <base />
        <rate-limit-by-key calls="1000" renewal-period="60" counter-key="@(context.Request.IpAddress)" />
        <quota-by-key calls="1000" renewal-period="600" counter-key="@(context.Request.IpAddress)" />
    </inbound>
        <backend>
                <forward-request />
        </backend>
        <outbound />
        <on-error />
</policies>"""

        def __init__(self):
            self.policy_file = os.path.join(TEST_DIR, self.POLICY_FILE_NAME).replace('\\', '\\\\')

        def delete_xml_file(self):
            os.remove(self.policy_file)

        def create_xml_file(self):
            self._ensure_data_dir()
            file = open(self.policy_file, "w")
            file.write(self.xml_content)
            file.close()

        def _ensure_data_dir(self):
            dirname = os.path.dirname(self.policy_file)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
