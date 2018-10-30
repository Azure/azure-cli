# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


def _get_test_data_file(filename):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'tests', 'latest', 'data', filename)
    open(filepath, 'r')
    return filepath
