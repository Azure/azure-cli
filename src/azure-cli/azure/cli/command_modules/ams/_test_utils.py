# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


def _get_test_data_file(filename):
    root_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
    return os.path.join(root_dir, 'tests', 'latest', 'data', filename)
