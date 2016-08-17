import os
import unittest
import mock
from six.moves import configparser
from azure.cli._config import AzConfigParser

class TestAzConfigParser(unittest.TestCase):

    def setUp(self):
        self.config = AzConfigParser()

    def test_has_option(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.config.add_section(section)
        self.config.set(section, option, value)
        self.assertTrue(self.config.has_option(section, option))

    @mock.patch.dict(os.environ, {AzConfigParser.env_var_name('MySection', 'myoption'): 'myvalue'})
    def test_has_option_env(self):
        section = 'MySection'
        option = 'myoption'
        self.assertTrue(self.config.has_option(section, option))

    def test_has_option_env_no(self):
        section = 'MySection'
        option = 'myoption'
        self.assertFalse(self.config.has_option(section, option))

    def test_get(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.config.add_section(section)
        self.config.set(section, option, value)
        self.assertEquals(self.config.get(section, option), value)

    @mock.patch.dict(os.environ, {AzConfigParser.env_var_name('MySection', 'myoption'): 'myvalue'})
    def test_get_env(self):
        section = 'MySection'
        option = 'myoption'
        value = 'myvalue'
        self.assertEquals(self.config.get(section, option), value)

    def test_get_not_found_section(self):
        section = 'MySection'
        option = 'myoption'
        with self.assertRaises(configparser.NoSectionError):
            self.config.get(section, option)

    def test_get_not_found_option(self):
        section = 'MySection'
        option = 'myoption'
        self.config.add_section(section)
        with self.assertRaises(configparser.NoOptionError):
            self.config.get(section, option)

    def test_get_fallback(self):
        section = 'MySection'
        option = 'myoption'
        self.assertEquals(self.config.get(section, option, fallback='fallback'), 'fallback')

    def test_getint(self):
        section = 'MySection'
        option = 'myoption'
        value = '123'
        self.config.add_section(section)
        self.config.set(section, option, value)
        self.assertEquals(self.config.getint(section, option), int(value))

    def test_getint_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_an_int'
        self.config.add_section(section)
        self.config.set(section, option, value)
        with self.assertRaises(ValueError):
            self.config.getint(section, option)

    def test_getfloat(self):
        section = 'MySection'
        option = 'myoption'
        value = '123.456'
        self.config.add_section(section)
        self.config.set(section, option, value)
        self.assertEquals(self.config.getfloat(section, option), float(value))

    def test_getfloat_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_float'
        self.config.add_section(section)
        self.config.set(section, option, value)
        with self.assertRaises(ValueError):
            self.config.getfloat(section, option)

    def test_getboolean(self):
        section = 'MySection'
        option = 'myoption'
        value = 'true'
        self.config.add_section(section)
        self.config.set(section, option, value)
        self.assertEquals(self.config.getboolean(section, option), True)

    def test_getboolean_error(self):
        section = 'MySection'
        option = 'myoption'
        value = 'not_a_boolean'
        self.config.add_section(section)
        self.config.set(section, option, value)
        with self.assertRaises(ValueError):
            self.config.getboolean(section, option)

if __name__ == '__main__':
    unittest.main()
