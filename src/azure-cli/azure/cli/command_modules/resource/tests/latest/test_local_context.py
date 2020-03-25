# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import ScenarioTest


class LocalContextScenarioTest(ScenarioTest):

    def test_resource_group_with_local_context(self):
        self.kwargs.update({
            'group': 'test_local_context_group',
            'location': 'eastasia'
        })
        self.cmd('local-context on')
        self.cmd('group create -n {group} -l {location}', checks=[self.check('name', self.kwargs['group'])])
        self.cmd('group show', checks=[
            self.check('name', self.kwargs['group']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('local-context off --yes')


if __name__ == '__main__':
    unittest.main()
