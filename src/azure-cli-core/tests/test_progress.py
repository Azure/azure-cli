# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock


class Test_Progress(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """ test the progress reporting """

    @mock.patch('azure.cli.core.progress', ...)
    def test_stuff(self):
        ''' Can get correct resource type API version '''
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(get_api_version(ResourceType.MGMT_STORAGE), '2020-10-10')

if __name__ == '__main__':
    unittest.main()
