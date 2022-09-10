# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import xmltodict
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimPolicyScenarioTest(ScenarioTest):
    xml_content = """<policies>
        <inbound></inbound>
        <backend>
                <!-- test -->
        </backend>
        <outbound />
        <on-error />
</policies>"""

    policy_file = os.path.join(TEST_DIR, 'data/policy.xml').replace('\\', '\\\\')

    def setUp(self):
        self._create_xml_file()
        super(ApimPolicyScenarioTest, self).setUp()

    def tearDown(self):
        self._delete_xml_file()
        super(ApimPolicyScenarioTest, self).tearDown()

    @ResourceGroupPreparer(name_prefix='cli_test_apim_policy-')
    @ApiManagementPreparer(sku_name='Consumption')
    def test_apim_policy(self):
        self.kwargs.update({
            'name': 'policy',
            'xml_value': self.xml_content,
            'xml_file': self.policy_file
        })

        self._create_policy_using_inline_xml()
        self._create_policy_using_xml_from_file()
        self._delete_policy_resets_xml_value()

    def _create_policy_using_inline_xml(self):
        cmd_statement = 'apim policy create -n {apim} -g {rg} -v "{xml_value}" --output tsv --query value'

        result = xmltodict.parse(self.cmd(cmd_statement).output)
        expected = xmltodict.parse(self.xml_content)

        self.assertDictEqual(expected, result)

    def _create_policy_using_xml_from_file(self):
        cmd_statement = 'apim policy create -n {apim} -g {rg} -f {xml_file} --output tsv --query value'

        result = xmltodict.parse(self.cmd(cmd_statement).output)
        expected = xmltodict.parse(self.xml_content)

        self.assertDictEqual(expected, result)

    def _delete_policy_resets_xml_value(self):
        self.cmd('apim policy delete -n {apim} -g {rg} --yes')

        with self.assertRaises(SystemExit):  # raises exit code 3 because of resource not found
            self.cmd('az apim policy show -n {apim} -g {rg}')

    def _delete_xml_file(self):
        os.remove(self.policy_file)

    def _create_xml_file(self):
        self._ensure_data_dir()
        file = open(self.policy_file, "w")
        file.write(self.xml_content)
        file.close()

    def _ensure_data_dir(self):
        dirname = os.path.dirname(self.policy_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
