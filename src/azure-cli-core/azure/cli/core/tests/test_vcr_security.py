# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest


class Test_vcr_security(unittest.TestCase):
    def test_deployment_name_scrub(self):
        from azure.cli.testsdk.vcr_test_base import _scrub_deployment_name as scrub_deployment_name
        uri1 = 'https://www.contoso.com/deployments/azurecli1466174372.33571889479?api-version=2015-11-01'
        uri2 = 'https://www.contoso.com/deployments/azurecli1466174372.33571889479/more'

        uri1 = scrub_deployment_name(uri1)
        uri2 = scrub_deployment_name(uri2)

        self.assertEqual(
            uri1, 'https://www.contoso.com/deployments/mock-deployment?api-version=2015-11-01')
        self.assertEqual(uri2, 'https://www.contoso.com/deployments/mock-deployment/more')


if __name__ == '__main__':
    unittest.main()
