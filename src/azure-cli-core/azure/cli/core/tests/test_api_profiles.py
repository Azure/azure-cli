# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.profiles import (ResourceType, PROFILE_TYPE, CustomResourceType,
                                     get_api_version, supported_api_version, register_resource_type)
from azure.cli.core.profiles._shared import APIVersionException, get_versioned_sdk_path
from azure.cli.core.cloud import Cloud
from azure.cli.core.mock import DummyCli


class TestAPIProfiles(unittest.TestCase):

    def test_get_api_version(self):
        # Can get correct resource type API version
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(get_api_version(cli, ResourceType.MGMT_STORAGE), '2020-10-10')

    def test_get_api_version_semver(self):
        # Can get correct resource type API version if semver used
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(get_api_version(cli, ResourceType.MGMT_KEYVAULT), '7.0')

    def test_get_api_version_invalid_rt(self):
        # Resource Type not in profile
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(cli, ResourceType.MGMT_COMPUTE)

    def test_get_api_version_invalid_active_profile(self):
        # The active profile is not in our profile dict
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='not-a-real-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(cli, ResourceType.MGMT_STORAGE)

    def test_supported_api_version_invalid_profile_name(self):
        # Invalid name for the profile name
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='not-a-real-profile')
        with self.assertRaises(ValueError):
            supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01')

    def test_get_api_version_invalid_rt_2(self):
        # None is not a valid resource type
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                get_api_version(cli, None)

    def test_supported_api_profile_no_constraints(self):
        # At least a min or max version must be specified
        cli = DummyCli()
        with self.assertRaises(ValueError):
            supported_api_version(cli, PROFILE_TYPE)

    def test_supported_api_profile_min_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile')
        self.assertTrue(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01'))

    def test_supported_api_profile_min_constraint_not_supported(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile-preview')
        self.assertFalse(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-02'))

    def test_supported_api_profile_min_max_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile')
        self.assertTrue(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01', max_api='2000-01-01'))

    def test_supported_api_profile_max_constraint_not_supported(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile')
        self.assertFalse(supported_api_version(cli, PROFILE_TYPE, max_api='1999-12-30'))

    def test_supported_api_profile_preview_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile')
        self.assertTrue(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01-preview'))

    def test_supported_api_profile_preview_constraint_in_profile(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2000-01-01-profile-preview')
        self.assertFalse(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01'))

    def test_supported_api_profile_latest(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='latest')
        self.assertTrue(supported_api_version(cli, PROFILE_TYPE, min_api='2000-01-01'))

    def test_supported_api_version_no_constraints(self):
        # At least a min or max version must be specified
        cli = DummyCli()
        with self.assertRaises(ValueError):
            supported_api_version(cli, ResourceType.MGMT_STORAGE)

    def test_supported_api_version_min_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_STORAGE, min_api='2000-01-01'))

    def test_supported_api_version_min_constraint_semver(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, min_api='6.0'))

    def test_supported_api_version_min_constraint_mixed_type(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, min_api='2016-06-04'))

    def test_supported_api_version_max_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_STORAGE, max_api='2021-01-01'))

    def test_supported_api_version_max_constraint_semver(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, max_api='8.0'))

    def test_supported_api_version_max_constraint_mixed_type(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '2016-06-04'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, max_api='8.0'))

    def test_supported_api_version_min_max_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(
                supported_api_version(cli, ResourceType.MGMT_STORAGE, min_api='2020-01-01', max_api='2021-01-01'))

    def test_supported_api_version_min_max_constraint_semver(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(
                supported_api_version(cli, ResourceType.MGMT_KEYVAULT, min_api='6.0', max_api='8.0'))

    def test_supported_api_version_max_constraint_not_supported(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_STORAGE, max_api='2019-01-01'))

    def test_supported_api_version_max_constraint_not_supported_semver(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, max_api='6.0'))

    def test_supported_api_version_max_constraint_not_supported_mixed_type(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, max_api='2016-07-01'))

    def test_supported_api_version_min_constraint_not_supported(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_STORAGE, min_api='2021-01-01'))

    def test_supported_api_version_min_constraint_not_supported_semver(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_KEYVAULT, min_api='8.0'))

    def test_supported_api_version_min_constraint_not_supported_mixed_type(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2016-06-04'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertFalse(supported_api_version(cli, ResourceType.MGMT_STORAGE, min_api='8.0'))

    def test_supported_api_version_preview_constraint(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10-preview'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertTrue(supported_api_version(cli, ResourceType.MGMT_STORAGE, min_api='2020-01-01'))

    def test_supported_api_version_invalid_rt_for_profile(self):
        cli = DummyCli()
        cli.cloud = Cloud('TestCloud', profile='2017-01-01-profile')
        test_profile = {'2017-01-01-profile': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            with self.assertRaises(APIVersionException):
                supported_api_version(cli, ResourceType.MGMT_COMPUTE, min_api='2020-01-01')

    def test_register_resource_type_valid(self):
        test_profile = {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles.API_PROFILES', test_profile):
            custom_rt = CustomResourceType('mysdkpath', 'myClient')
            register_resource_type('latest', custom_rt, '2020-12-12-preview')
            from azure.cli.core.profiles import API_PROFILES
            self.assertDictEqual(API_PROFILES, {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10',
                                                           custom_rt: '2020-12-12-preview'}})

    def test_register_resource_type_bad_profile(self):
        test_profile = {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles.API_PROFILES', test_profile):
            custom_rt = CustomResourceType('mysdkpath', 'myClient')
            with self.assertRaises(ValueError):
                register_resource_type('doesnotexist', custom_rt, '2020-12-12-preview')

    def test_register_resource_type_bad_rt_string(self):
        test_profile = {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles.API_PROFILES', test_profile):
            with self.assertRaises(TypeError):
                register_resource_type('doesnotexist', 'ResourceType.MGMT_STORAGE', '2020-12-12-preview')

    def test_register_resource_type_bad_rt_attempted_override(self):
        test_profile = {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles.API_PROFILES', test_profile):
            with self.assertRaises(TypeError):
                register_resource_type('doesnotexist', ResourceType.MGMT_STORAGE, '2020-12-12-preview')

    def test_get_versioned_sdk_path_date(self):
        test_profile = {'latest': {ResourceType.MGMT_STORAGE: '2020-10-10'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(
                get_versioned_sdk_path('latest', ResourceType.MGMT_STORAGE),
                "azure.mgmt.storage.v2020_10_10"
            )

    def test_get_versioned_sdk_path_semver(self):
        test_profile = {'latest': {ResourceType.DATA_KEYVAULT: '7.0'}}
        with mock.patch('azure.cli.core.profiles._shared.AZURE_API_PROFILES', test_profile):
            self.assertEqual(
                get_versioned_sdk_path('latest', ResourceType.DATA_KEYVAULT),
                "azure.keyvault.v7_0"
            )


if __name__ == '__main__':
    unittest.main()
