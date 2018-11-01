import unittest
from azure.cli.command_modules.vm._vm_utils import get_sku_dict_from_string
from knack.util import CLIError


class TestSKUParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sku_tests = {"test_empty": ("", {}),
                         "test_all": ("sku", {"all": "sku"}),
                         "test_os": ("os=sku", {"os": "sku"}),
                         "test_lun": ("1=sku", {1: "sku"}),
                         "test_os_lun": ("os=sku 1=sku_1", {"os": "sku", 1: "sku_1"}),
                         "test_os_mult_lun": ("1=sku_1 os=sku_os 2=sku_2", {1: "sku_1", "os": "sku_os", 2: "sku_2"}),
                         "test_double_equ": ("os==foo", {"os": "=foo"}),
                         "test_err_no_eq": ("os=sku_1 foo", None),
                         "test_err_lone_eq": ("foo =", None),
                         "test_err_float": ("2.7=foo", None),
                         "test_err_bad_key": ("bad=foo", None)}

    def test_all(self):
        for test_str, expected in self.sku_tests.values():
            if isinstance(expected, dict):
                result = get_sku_dict_from_string(test_str)
                self.assertEqual(result, expected)
            elif expected is None:
                with self.assertRaises(CLIError):
                    get_sku_dict_from_string(test_str)
            else:
                self.fail()
