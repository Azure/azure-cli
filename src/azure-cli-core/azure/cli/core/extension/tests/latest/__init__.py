# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import tempfile
import shutil


def get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


class ExtensionTypeTestMixin(unittest.TestCase):

    def setUp(self):
        self.ext_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.ext_dir, ignore_errors=True)
