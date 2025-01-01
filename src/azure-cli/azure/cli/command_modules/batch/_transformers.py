# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import todict
from azure.core.paging import ItemPaged
import unittest

transform_map = {
    "etag": "eTag",
    "logicalUnitNumber": "lun"
}

def transform_object(result):

    new_dict = {}

    # print(result)
    
    for key, value in result.items():
                    
        new_key = transform_map[key] if key in transform_map else key

        if isinstance(value, dict):
            new_dict[new_key] = transform_object(value)
        elif isinstance(value, list): # if another dictionary is in a list then we should check to transform
            new_dict[new_key] = transform_object_list(value)
        else:
            new_dict[new_key] = value

    return new_dict

def transform_object_list(result):
    new_result = []
    result_list = list(result) if isinstance(result, ItemPaged) else result
    for item in result_list:
        updated_obj = transform_object(item)

        # print(updated_obj)

        new_result.append(updated_obj)
    return new_result


# Quick tests

fake_etag_json = {
    "etag": {
        "id": "task_123",
        "displayName": "example",
        "etag": [
            {"etag": "tag"}
        ],
        "requiredSlots": 2
    }
}

fake_lun_json = {
    "logicalUnitNumber": {
        "potato": "french fries",
        "logicalUnitNumber": 123
    }
}

class TestTransform(unittest.TestCase):
    def test_transform(self):
        update_etag = transform_object(fake_etag_json)
        update_lun = transform_object(fake_lun_json)

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
