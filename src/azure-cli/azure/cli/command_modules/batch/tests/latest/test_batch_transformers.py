# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#

import unittest

from azure.cli.command_modules.batch._transformers import Transformer
from azure.batch.models import BatchJobConstraints


class TestBatchTransformers(unittest.TestCase):

    def test_transform_object_empty_list(self):
        fake_transformer = Transformer({"testing": "potato"})
        result = fake_transformer.transform_result([])
        self.assertEqual(result, [])
    
    def test_transform_object(self):
        fake_transformer = Transformer({"testing": "potato"})

        fake_potato_json = {
            "testing": "fake_potato"
        }

        transformed_potato_json = {
            "potato": "fake_potato"
        }

        result = fake_transformer.transform_result(fake_potato_json)
        self.assertEqual(result, transformed_potato_json)

    def test_transform_object_list(self):
        fake_transformer = Transformer({"testing": "potato"})
        fake_potato_json = {
            "testing": "fake_potato"
        }

        transformed_potato_json = {
            "potato": "fake_potato"
        }

        result = fake_transformer.transform_result([fake_potato_json])
        self.assertEqual(result, [transformed_potato_json])

    def test_transform_nested_object(self):
        fake_transformer = Transformer({"testing": "potato"})
        fake_potato_json = {
            "testing": {
                "id": "task_123",
                "displayName": "example",
                "testing": "fake_potato",
                "requiredSlots": 2
            }
        }

        transformed_potato_json = {
            "potato": {
                "id": "task_123",
                "displayName": "example",
                "potato": "fake_potato",
                "requiredSlots": 2
            }
        }

        result = fake_transformer.transform_result([fake_potato_json])
        self.assertEqual(result, [transformed_potato_json])
    
    def test_transform_model_object(self):

        fake_transform_map = {
            "maxTaskRetryCount": "banana",
            "constraints": "cauliflower",
            "testing": "potato"
        }

        fake_transformer = Transformer(fake_transform_map)

        job_constraints = BatchJobConstraints(
            max_wall_clock_time="P10675199DT2H48M5.4775807S",
            max_task_retry_count=0
        )

        fake_potato_json = {
            "testing": {
                "id": "task_123",
                "displayName": "example",
                "constraints": job_constraints,
                "requiredSlots": 2
            }
        }

        transformed_potato_json = {
            "potato": {
                "id": "task_123",
                "displayName": "example",
                "cauliflower": {
                    "banana": 0,
                    "maxWallClockTime": "P10675199DT2H48M5.4775807S",
                },
                "requiredSlots": 2
            }
        }

        result = fake_transformer.transform_result([fake_potato_json])
        self.assertEqual(result, [transformed_potato_json])
