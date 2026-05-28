#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from azure.cli.command_modules.container._params import _environment_variables_type, _secure_environment_variables_type


class ContainerParamsTest(unittest.TestCase):

    def test_environment_variables_type_preserves_special_characters(self):
        env = _environment_variables_type('APP_DB_PASSWORD=wada"wada^')
        self.assertEqual(env['name'], 'APP_DB_PASSWORD')
        self.assertEqual(env['value'], 'wada"wada^')

        payload = json.dumps({'environmentVariables': [env]})
        self.assertIn('wada\\"wada^', payload)

    def test_secure_environment_variables_type_preserves_special_characters(self):
        env = _secure_environment_variables_type('APP_DB_PASSWORD=wada"wada^')
        self.assertEqual(env['name'], 'APP_DB_PASSWORD')
        self.assertEqual(env['secureValue'], 'wada"wada^')

        payload = json.dumps({'environmentVariables': [env]})
        self.assertIn('wada\\"wada^', payload)


if __name__ == '__main__':
    unittest.main()
