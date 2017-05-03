from azure.cli.testsdk import ScenarioTest, JMESPathCheck


class CdnEndpointScenarioTest(ScenarioTest):
    def test_edge_node_crud(self):
        checks = [JMESPathCheck('value.length(@)', 3)]
        self.cmd('cdn edge-node list', checks=checks)
