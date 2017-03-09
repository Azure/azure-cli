# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock
import os.path
from six import StringIO

from azure.cli.command_modules.resource._validators import validate_deployment_name

class Test_resource_validators(unittest.TestCase):

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_generate_deployment_name_from_file(self):
        #verify auto-gen from uri
        namespace = mock.MagicMock()
        namespace.template_uri = 'https://templates/template123.json?foo=bar'
        namespace.template_file = None
        namespace.deployment_name = None
        validate_deployment_name(namespace)
        self.assertEqual('template123', namespace.deployment_name)

        namespace = mock.MagicMock()
        namespace.template_file = __file__
        namespace.template_uri = None
        namespace.deployment_name = None
        validate_deployment_name(namespace)
        self.assertEqual(os.path.basename(__file__)[:-3], namespace.deployment_name)

        #verify use default if get a file content
        namespace = mock.MagicMock()
        namespace.template_file = '{"foo":"bar"}'
        namespace.template_uri = None
        namespace.deployment_name = None
        validate_deployment_name(namespace)
        self.assertEqual('deployment1', namespace.deployment_name)

if __name__ == '__main__':
    unittest.main()
