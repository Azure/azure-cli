# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse


class securitySolutionsReferenceDataTests(ScenarioTest):

    def test_security_securitySolutionsReferenceData(self):

        SolutionsReferenceData = self.cmd('az security security_solutions_reference_data list').get_output_in_json()

        assert len(SolutionsReferenceData) >= 0

        self.cmd('az security security_solutions_reference_data list')
