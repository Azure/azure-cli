# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# flake8: noqa

import os
import stat
import unittest
import tempfile
import mock
from six.moves import configparser
from azure.cli.core._config import CONFIG_FILE_NAME, AzConfig, set_global_config_value


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


class TestSetConfig(unittest.TestCase):

    def setUp(self):
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, CONFIG_FILE_NAME)

    def test_set_config_value(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            config = configparser.SafeConfigParser()
            config.read(os.path.join(self.config_dir, CONFIG_FILE_NAME))
            self.assertEqual(config.get('test_section', 'test_option'), 'a_value')

    def test_set_config_value_duplicate_section_ok(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            set_global_config_value('test_section', 'test_option_another', 'another_value')
            config = configparser.SafeConfigParser()
            config.read(os.path.join(self.config_dir, CONFIG_FILE_NAME))
            self.assertEqual(config.get('test_section', 'test_option'), 'a_value')
            self.assertEqual(config.get('test_section', 'test_option_another'), 'another_value')

    def test_set_config_value_not_string(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path), \
        self.assertRaises(TypeError):
            set_global_config_value('test_section', 'test_option', False)

    def test_set_config_value_file_permissions(self):
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
        mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):
            set_global_config_value('test_section', 'test_option', 'a_value')
            file_mode = os.stat(self.config_path).st_mode
            self.assertTrue(bool(file_mode & stat.S_IRUSR))
            self.assertTrue(bool(file_mode & stat.S_IWUSR))
            self.assertFalse(bool(file_mode & stat.S_IXUSR))
            self.assertFalse(bool(file_mode & stat.S_IRGRP))
            self.assertFalse(bool(file_mode & stat.S_IWGRP))
            self.assertFalse(bool(file_mode & stat.S_IXGRP))
            self.assertFalse(bool(file_mode & stat.S_IROTH))
            self.assertFalse(bool(file_mode & stat.S_IWOTH))
            self.assertFalse(bool(file_mode & stat.S_IXOTH))


if __name__ == '__main__':
    unittest.main()
