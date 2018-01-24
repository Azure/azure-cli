# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest


class CdnEdgeNodecenarioTest(ScenarioTest):
    def test_edge_node_crud(self):
        self.cmd('cdn edge-node list', checks=self.check('length(@)', 3))
