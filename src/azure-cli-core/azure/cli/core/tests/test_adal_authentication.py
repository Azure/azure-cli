# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
from azure.cli.core.adal_authentication import _try_scopes_to_resource


class TestUtils(unittest.TestCase):

    def test_try_scopes_to_resource(self):
        # Test no scopes
        self.assertIsNone(_try_scopes_to_resource(()))
        self.assertIsNone(_try_scopes_to_resource([]))
        self.assertIsNone(_try_scopes_to_resource(None))

        # Test multiple scopes, with the first one discarded
        resource = _try_scopes_to_resource(("https://management.core.windows.net//.default",
                                            "https://management.core.chinacloudapi.cn//.default"))
        self.assertEqual(resource, "https://management.core.chinacloudapi.cn/")

        # Test single scopes (the correct usage)
        resource = _try_scopes_to_resource(("https://management.core.chinacloudapi.cn//.default",))
        self.assertEqual(resource, "https://management.core.chinacloudapi.cn/")


if __name__ == '__main__':
    unittest.main()
