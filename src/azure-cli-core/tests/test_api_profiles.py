# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.core.profiles import (get_api_version,
                                     supported_api_version,
                                     PROFILE_TYPE,
                                     ResourceType)
from azure.cli.core.profiles._shared import APIVersionException
from azure.cli.core.cloud import Cloud


class TestAPIProfiles(unittest.TestCase):

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_get_api_version(self):
        ''' Can get correct resource type API version '''
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(get_api_version(ResourceType.MGMT_STORAGE), '2020-10-10')

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_get_api_version_invalid_rt(self):
        ''' Resource Type not in profile '''
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(ResourceType.MGMT_COMPUTE)

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='not-a-real-profile'))
    def test_get_api_version_invalid_active_profile(self):
        ''' The active profile is not in our profile dict '''
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(ResourceType.MGMT_STORAGE)

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_get_api_version_invalid_rt_2(self):
        ''' None is not a valid resource type '''
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(None)

    def test_supported_api_profile_no_constraints(self):
        ''' At least a min or max version must be specified '''
        with self.assertRaises(ValueError):
            supported_api_version(PROFILE_TYPE)

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='2000-01-01'))
    def test_supported_api_profile_min_constraint(self):
        self.assertTrue(supported_api_version(PROFILE_TYPE, min_api='2000-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='2000-01-01'))
    def test_supported_api_profile_min_constraint_not_supported(self):
        self.assertFalse(supported_api_version(PROFILE_TYPE, min_api='2000-01-02'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='2000-01-01'))
    def test_supported_api_profile_min_max_constraint(self):
        self.assertTrue(supported_api_version(PROFILE_TYPE,
                                              min_api='2000-01-01',
                                              max_api='2000-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='2000-01-01'))
    def test_supported_api_profile_max_constraint_not_supported(self):
        self.assertFalse(supported_api_version(PROFILE_TYPE, max_api='1999-12-30'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='2000-01-01'))
    def test_supported_api_profile_preview_constraint(self):
        self.assertTrue(supported_api_version(PROFILE_TYPE, min_api='2000-01-01-preview'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='latest'))
    def test_supported_api_profile_latest(self):
        self.assertTrue(supported_api_version(PROFILE_TYPE, min_api='2000-01-01'))

    def test_supported_api_version_no_constraints(self):
        ''' At least a min or max version must be specified '''
        with self.assertRaises(ValueError):
            supported_api_version(ResourceType.MGMT_STORAGE)

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_min_constraint(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(ResourceType.MGMT_STORAGE, min_api='2000-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_max_constraint(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(ResourceType.MGMT_STORAGE, max_api='2021-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_min_max_constraint(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(ResourceType.MGMT_STORAGE,
                                                  min_api='2020-01-01',
                                                  max_api='2021-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_max_constraint_not_supported(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(ResourceType.MGMT_STORAGE, max_api='2019-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_min_constraint_not_supported(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(ResourceType.MGMT_STORAGE, min_api='2021-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_preview_constraint(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10-preview'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(ResourceType.MGMT_STORAGE, min_api='2020-01-01'))

    @mock.patch('azure.cli.core._profile.CLOUD', Cloud('TestCloud', profile='myprofile'))
    def test_supported_api_version_invalid_rt_for_profile(self):
        test_profile = {'myprofile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2020-01-01')


if __name__ == '__main__':
    unittest.main()
