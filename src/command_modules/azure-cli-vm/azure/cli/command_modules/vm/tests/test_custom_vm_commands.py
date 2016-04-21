import json
import unittest
from azure.cli.command_modules.vm.custom import MinMaxValue

class Test_Vm_Custom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_custom_minmax(self):
        validator = MinMaxValue(1, 3)
        self.assertEqual(1, validator(1))
        self.assertEqual(2, validator(2))
        self.assertEqual(3, validator(3))
        self.assertEqual(1, validator('1'))
        self.assertEqual(2, validator('2'))
        self.assertEqual(3, validator('3'))
        with self.assertRaises(ValueError):
            validator(0)
        with self.assertRaises(ValueError):
            validator('0')
        with self.assertRaises(ValueError):
            validator(4)
        with self.assertRaises(ValueError):
            validator('4')

if __name__ == '__main__':
    unittest.main()
