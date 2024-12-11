# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import todict
import unittest

class Transformer:

    transform_map = {
        "etag": "eTag",
        "logicalUnitNumber": "lun"
    }

    def transform_take2(self, result):

        new_dict = {}
        
        for key, value in result.items():
                        
            new_key = self.transform_map[key] if key in self.transform_map else key

            if isinstance(value, dict):
                transformed_dict = self.transform_take2(value)
                new_dict[new_key] = transformed_dict
            else:
                new_dict[new_key] = value

        return new_dict


    fake_t2_json_result = {
        "etag": {
            "id": "task_123",
            "displayName": "example",
            "etag": "tag",
            "requiredSlots": 2
        }
    }

    fake_t2_take2 = {
        "logicalUnitNumber": {
            "potato": "french fries",
            "logicalUnitNumber": 123
        }
    }


class TestTransform(unittest.TestCase):
    def test_transform(self):
        update_etag = Transformer().transform_take2(Transformer().fake_t2_json_result)
        update_lun = Transformer().transform_take2(Transformer().fake_t2_take2)

        # self.assertEqual(
        #     {
        #         "id": "task_123",
        #         "displayName": "example",
        #         "eTag": "tag",
        #         "requiredSlots": 2
        #     },
        #     update_etag
        # )
        print(update_etag)
        print(update_lun)

if __name__ == '__main__':
    unittest.main()
