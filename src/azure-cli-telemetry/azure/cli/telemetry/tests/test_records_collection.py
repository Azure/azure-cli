# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import tempfile
import unittest

from azure.cli.telemetry.const import TELEMETRY_CACHE_DIR
from azure.cli.telemetry.components.records_collection import RecordsCollection


class TestRecordsCollection(unittest.TestCase):
    TEST_RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), 'resources')
    TEST_CACHE_FILE_COUNT = len(os.listdir(TEST_RESOURCE_FOLDER))

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        shutil.copytree(self.TEST_RESOURCE_FOLDER, os.path.join(self.work_dir, TELEMETRY_CACHE_DIR))

        self.assert_cache_files_count(self.TEST_CACHE_FILE_COUNT)

    def tearDown(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def test_create_records_collection(self):
        collection = RecordsCollection(os.path.join(self.work_dir, TELEMETRY_CACHE_DIR))

        # cache files are not moved while the collection is created
        self.assert_cache_files_count(self.TEST_CACHE_FILE_COUNT)

        # take snapshot and move the files
        collection.snapshot_and_read()

        # all files are moved, including the directory.
        self.assertFalse(os.path.exists(os.path.join(self.work_dir, TELEMETRY_CACHE_DIR)))

        # total records
        self.assertEqual(1758, len([r for r in collection]))

    def test_create_records_collection_against_empty_folder(self):
        collection = RecordsCollection(tempfile.mktemp())
        self.assertEqual(0, len([r for r in collection]))

    def assert_cache_files_count(self, count):
        self.assertEqual(len(os.listdir(os.path.join(self.work_dir, TELEMETRY_CACHE_DIR))),
                         count)


if __name__ == '__main__':
    unittest.main()
