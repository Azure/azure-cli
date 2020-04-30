# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.local_context import AzCLILocalContext, ALL


class TestLocalContext(unittest.TestCase):

    @unittest.skip("will roll back when TurnOnLocalContext annotation is ready")
    def test_local_context(self):
        self.assertTrue(self.local_context.is_on)
        self.local_context.set([ALL], 'resource_group_name', 'test_rg')
        self.assertEqual('test_rg', self.local_context.get('vm create', 'resource_group_name'))
        self.assertEqual(self.working_dir, self.local_context.current_turn_on_dir())


if __name__ == '__main__':
    unittest.main()
