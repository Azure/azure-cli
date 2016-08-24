#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import unittest
import mock
from six.moves import configparser
from azure.cli._config import AzConfig

class TestAzConfig(unittest.TestCase):

    def setUp(self):
        self.az_config = AzConfig()

    def test_has_option(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        self.assertTrue(self.az_config.has_option(section, option))

    @mock.patch.dict(os.environ, {AzConfig.env_var_name('MySection', 'myoption'): 'myvalue'})
    def test_has_option_env(self):
        section = 'MySection'
        option = 'myoption'
        self.assertTrue(self.az_config.has_option(section, option))

    def test_has_option_env_no(self):
        section = 'MySection'
        option = 'myoption'
        self.assertFalse(self.az_config.has_option(section, option))

    def test_get(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        self.assertEqual(self.az_config.get(section, option), value)

    @mock.patch.dict(os.environ, {AzConfig.env_var_name('MySection', 'myoption'): 'myvalue'})
    def test_get_env(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.assertEqual(self.az_config.get(section, option), value)

    def test_get_not_found_section(self):
        section = 'MySection'
        option = 'myoption'
        with self.assertRaises(configparser.NoSectionError):
            self.az_config.get(section, option)

    def test_get_not_found_option(self):
        section = 'MySection'
        option = 'myoption'
        self.az_config.config_parser.add_section(section)
        with self.assertRaises(configparser.NoOptionError):
            self.az_config.get(section, option)

    def test_get_fallback(self):
        section = 'MySection'
        option = 'myoption'
        self.assertEqual(self.az_config.get(section, option, fallback='fallback'), 'fallback')

    def test_getint(self):
        section = 'MySection'
        option = 'myoption'
        value = '123'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        self.assertEqual(self.az_config.getint(section, option), int(value))

    def test_getint_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_an_int'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        with self.assertRaises(ValueError):
            self.az_config.getint(section, option)

    def test_getfloat(self):
        section = 'MySection'
        option = 'myoption'
        value = '123.456'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        self.assertEqual(self.az_config.getfloat(section, option), float(value))

    def test_getfloat_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_float'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        with self.assertRaises(ValueError):
            self.az_config.getfloat(section, option)

    def test_getboolean(self):
        section = 'MySection'
        option = 'myoption'
        value = 'true'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        self.assertEqual(self.az_config.getboolean(section, option), True)

    def test_getboolean_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_boolean'
        self.az_config.config_parser.add_section(section)
        self.az_config.config_parser.set(section, option, value)
        with self.assertRaises(ValueError):
            self.az_config.getboolean(section, option)

if __name__ == '__main__':
    unittest.main()
