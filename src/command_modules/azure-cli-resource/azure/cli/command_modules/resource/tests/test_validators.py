#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import unittest
from six import StringIO

from azure.cli.core.commands.validators import *

from azure.cli.command_modules.resource._validators import *

class Test_resource_validators(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.io = StringIO()
        
    def tearDown(self):
        self.io.close()

    def test_resource_type_valid(self):
        input = 'Test.Namespace/testtype'
        actual = validate_resource_type(input)
        self.assertEqual(actual.namespace, 'Test.Namespace')
        self.assertEqual(actual.type, 'testtype')

    def test_resource_type_invalid(self):
        pass

    def test_parent_valid(self):
        input = 'testtype/mytesttype'
        actual = validate_parent(input)
        self.assertEqual(actual.type, 'testtype')
        self.assertEqual(actual.name, 'mytesttype')        

    def test_parent_invalid(self):
        pass

if __name__ == '__main__':
    unittest.main()
