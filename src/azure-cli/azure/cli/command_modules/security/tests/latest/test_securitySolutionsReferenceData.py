# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class securitySolutionsReferenceDataTests(ScenarioTest):

    def test_security_securitySolutionsReferenceData(self):

        SolutionsReferenceData = self.cmd('az security security-solutions-reference-data list').get_output_in_json()

        assert len(SolutionsReferenceData) >= 0

        self.cmd('az security security-solutions-reference-data list')