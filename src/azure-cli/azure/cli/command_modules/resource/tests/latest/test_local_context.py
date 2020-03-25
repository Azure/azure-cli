# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import tempfile

from azure.cli.testsdk import ScenarioTest


class LocalContextScenarioTest(ScenarioTest):

    def test_resource_group_with_local_context(self):
        self.kwargs.update({
            'group': 'test_local_context_group',
            'location': 'eastasia'
        })
        original_working_dir = os.getcwd()
        working_dir = tempfile.mkdtemp()
        os.chdir(working_dir)
        self.cmd('local-context on')
        self.cmd('group create -n {group} -l {location}', checks=[self.check('name', self.kwargs['group'])])
        self.cmd('group show', checks=[
            self.check('name', self.kwargs['group']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('local-context off --yes')
        os.chdir(original_working_dir)


if __name__ == '__main__':
    unittest.main()
