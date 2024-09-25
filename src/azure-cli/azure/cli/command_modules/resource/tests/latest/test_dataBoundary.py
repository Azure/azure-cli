from azure.cli.testsdk import ScenarioTest, record_only, live_only
import pytest

class AzureDataBoundaryScenarioTest(ScenarioTest):

    def test_get_tenant(self):
        # just make sure this doesn't throw
        self.cmd('az resources data-boundary show').get_output_in_json()