# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.testsdk import ScenarioTest


class LogAnalyticsDataClientTests(ScenarioTest):
    """Test class for Log Analytics data client."""
    def test_query(self):
        """Tests data plane query capabilities for Log Analytics."""
        self.cmd('az loganalytics query -w cab864ad-d0c1-496b-bc5e-4418315621bf --kql "Heartbeat | getschema"', checks=[
            self.check('tables[0].rows[0][0]', 'TenantId')
        ])
        query_result = self.cmd('az loganalytics query -w cab864ad-d0c1-496b-bc5e-4418315621bf --kql "Heartbeat | getschema"').get_output_in_json()
        assert len(query_result['tables'][0]['rows']) == 29
        assert isinstance(query_result['tables'][0]['rows'][0][1], (int, float, complex))
