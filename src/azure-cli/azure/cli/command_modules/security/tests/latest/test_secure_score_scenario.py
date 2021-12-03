# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenteSecureScoreTests(ScenarioTest):

    @AllowLargeResponse()
    def test_security_secure_score(self):

        scores_list = self.cmd('az security secure-scores list').get_output_in_json()
        assert len(scores_list) > 0

        ascScore = self.cmd('az security secure-scores show --n "ascScore"').get_output_in_json()
        assert len(ascScore) > 0

        controls_list = self.cmd('az security secure-score-controls list').get_output_in_json()
        assert len(controls_list) > 0

        controls_by_score_list = self.cmd('az security secure-score-controls list_by_score --n "ascScore"').get_output_in_json()
        assert len(controls_by_score_list) > 0

        control_definitions = self.cmd('az security secure-score-control-definitions list').get_output_in_json()
        assert len(control_definitions) > 0
