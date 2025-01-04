# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import Mapping, Iterable
from knack.util import todict
from azure.core.paging import ItemPaged
from msrest.serialization import Model
import unittest
import json

class Transformer:

    def __init__(self, transform_mapping):
        self.transform_mapping = transform_mapping


    def transform_object(self, result):

        new_dict = {}

        # print(type(result))
        # print(result)
        # print("before for loop")
        
        for key, value in result.items():
                        
            new_key = self.transform_mapping[key] if key in self.transform_mapping else key

            # print(new_key)
            # print(type(value))

            if isinstance(value, Mapping):
                print("blah")
                new_dict[new_key] = self.transform_object(value)
            # elif isinstance(value, Iterable): # if another dictionary is in a list then we should check to transform
            #     new_dict[new_key] = transform_object_list(value)
            else:
                new_dict[new_key] = value

        return new_dict

    def transform_object_list(self, result):
        new_result = []

        result_list = list(result) if isinstance(result, ItemPaged) else result

        for item in result_list:
            updated_obj = self.transform_object(item)
            new_result.append(updated_obj)
        return new_result


transform_map = {
    # "etag": "eTag",
    "logicalUnitNumber": "lun",
    # "userIdentity": "potato",
    # "maxTaskRetryCount": "banana",
    # "constraints": "cauliflower",
    # "testing": "potato"
    "id": "broccoli"
}

batch_transformer = Transformer(transform_map)
