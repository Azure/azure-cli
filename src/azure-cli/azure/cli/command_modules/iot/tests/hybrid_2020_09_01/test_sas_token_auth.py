# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.iot.sas_token_auth import SasTokenAuthentication


class TestSasTokenAuth(unittest.TestCase):
    def test_generate_sas_token(self):
        # Prepare parameters
        uri = 'iot-hub-for-test.azure-devices.net/devices/iot-device-for-test'
        policy_name = 'iothubowner'
        access_key = '+XLy+MVZ+aTeOnVzN2kLeB16O+kSxmz6g3rS6fAf6rw='
        expiry = 1471940363

        # Action
        sas_auth = SasTokenAuthentication(uri, policy_name, access_key, expiry)
        token = sas_auth.generate_sas_token()

        # Assertion
        self.assertIn('SharedAccessSignature ', token)
        self.assertIn('sig=RTNrGy6n%2Fs2uLLZFuVHBIJtdxIJP1LuKfhKjHwwbu7A%3D', token)
        self.assertIn('se=1471940363', token)
        self.assertIn('sr=iot-hub-for-test.azure-devices.net%252fdevices%252fiot-device-for-test',
                      token)
        self.assertIn('skn=iothubowner', token)


if __name__ == '__main__':
    unittest.main()
