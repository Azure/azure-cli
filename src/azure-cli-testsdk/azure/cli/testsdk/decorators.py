# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from .const import ENV_LIVE_TEST


def live_only():
    return unittest.skipUnless(
        os.environ.get(ENV_LIVE_TEST, False),
        'This test is designed to live test only.')
