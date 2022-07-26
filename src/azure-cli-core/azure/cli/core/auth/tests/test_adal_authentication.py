# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.auth.adal_authentication import _normalize_expires_on


class TestUtil(unittest.TestCase):
    def test_normalize_expires_on(self):
        assert _normalize_expires_on("11/05/2021 15:18:31 +00:00") == 1636125511
        assert _normalize_expires_on('1636125511') == 1636125511


if __name__ == '__main__':
    unittest.main()
