# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.container import custom as container_custom
from azure.cli.command_modules.container._params import _environment_variables_type


class ContainerParamsTests(unittest.TestCase):

    def test_environment_variables_type_preserves_quotes_and_carets(self):
        result = _environment_variables_type('APP_DB_PASSWORD=wada"wada^')

        self.assertEqual(result, {
            'name': 'APP_DB_PASSWORD',
            'value': 'wada"wada^'
        })

    @mock.patch.dict('os.environ', {'APP_DB_PASSWORD': 'wada"wada^'}, clear=False)
    def test_yaml_env_var_constructor_preserves_quotes_and_carets(self):
        result = container_custom.yaml.safe_load("""
value: ${APP_DB_PASSWORD}
""")

        self.assertEqual(result['value'], 'wada"wada^')
