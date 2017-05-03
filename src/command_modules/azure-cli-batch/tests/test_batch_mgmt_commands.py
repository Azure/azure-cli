# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import os
import mock

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                                     NoneCheck)
from azure.cli.core._config import az_config, CONFIG_FILE_NAME


def _before_record_response(response):
    # ignore any 401 responses during playback
    if response['status']['code'] == 401:
        response = None
    return response


class BatchMgmtAccountScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def tear_down(self):
        rg = self.resource_group
        name = self.storage_account_name
        self.cmd('storage account delete -g {} -n {} --yes'.format(rg, name))

    def __init__(self, test_method):
        super(BatchMgmtAccountScenarioTest, self).__init__(__file__, test_method)
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, CONFIG_FILE_NAME)
        self.resource_group = 'vcr_resource_group'
        self.account_name = 'clibatchtest1'
        self.byos_account_name = 'clibatchtestuser1'
        self.location = 'brazilsouth'
        self.byos_location = 'uksouth'
        self.storage_account_name = 'clibatchteststorage1'
        self.keyvault_name = 'clibatchtestkeyvault1'
        self.object_id = 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a'

    def test_batch_account_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        name = self.account_name
        loc = self.location

        # test create storage account with default set
        result = self.cmd('storage account create -g {} -n {} -l {} --sku Standard_LRS'.
                          format(rg, self.storage_account_name, loc),
                          checks=[JMESPathCheck('name', self.storage_account_name),
                                  JMESPathCheck('location', loc),
                                  JMESPathCheck('resourceGroup', rg)])
        sid = result['id']

        # test create keyvault for use with BYOS account
        self.cmd('keyvault create -g {} -n {} -l {} --enabled-for-deployment true '
                 '--enabled-for-disk-encryption true --enabled-for-template-deployment'
                 ' true'.format(rg, self.keyvault_name, self.byos_location),
                 checks=[JMESPathCheck('name', self.keyvault_name),
                         JMESPathCheck('location', self.byos_location),
                         JMESPathCheck('resourceGroup', rg),
                         JMESPathCheck('type(properties.accessPolicies)', 'array'),
                         JMESPathCheck('length(properties.accessPolicies)', 1),
                         JMESPathCheck('properties.sku.name', 'standard')])
        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions all '
                 '--secret-permissions all'.format(rg, self.keyvault_name, self.object_id))

        # test create account with default set
        self.cmd('batch account create -g {} -n {} -l {}'.format(rg, name, loc), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg)
        ])

        # test create account with BYOS
        self.cmd('batch account create -g {} -n {} -l {} --keyvault {}'.
                 format(rg, self.byos_account_name, self.byos_location, self.keyvault_name),
                 checks=[JMESPathCheck('name', self.byos_account_name),
                         JMESPathCheck('location', self.byos_location),
                         JMESPathCheck('resourceGroup', rg)])

        self.cmd('batch account set -g {} -n {} --storage-account {}'.
                 format(rg, name, self.storage_account_name),
                 checks=[JMESPathCheck('name', name),
                         JMESPathCheck('location', loc),
                         JMESPathCheck('resourceGroup', rg)])

        self.cmd('batch account show -g {} -n {}'.format(rg, name),
                 checks=[JMESPathCheck('name', name),
                         JMESPathCheck('location', loc),
                         JMESPathCheck('resourceGroup', rg),
                         JMESPathCheck('autoStorage.storageAccountId', sid)])

        self.cmd('batch account autostorage-keys sync -g {} -n {}'.format(rg, name))

        keys = self.cmd('batch account keys list -g {} -n {}'.format(rg, name),
                        checks=[JMESPathCheck('primary != null', True),
                                JMESPathCheck('secondary != null', True)])

        keys2 = self.cmd('batch account keys renew -g {} -n {} --key-name primary'.
                         format(rg, name),
                         checks=[JMESPathCheck('primary != null', True),
                                 JMESPathCheck('secondary', keys['secondary'])])

        self.assertTrue(keys['primary'] != keys2['primary'])

        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.config_dir), \
             mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', self.config_path):  # noqa: F122
            self.cmd('batch account login -g {} -n {}'.
                     format(rg, name), checks=NoneCheck())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'aad')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), name)
            self.assertFalse(az_config.config_parser.has_option('batch', 'access_key'))

            self.cmd('batch account login -g {} -n {} --shared-key-auth'.
                     format(rg, name), checks=NoneCheck())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'shared_key')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), name)
            self.assertEqual(az_config.config_parser.get('batch', 'access_key'), keys2['primary'])

        # test batch account delete
        self.cmd('batch account delete -g {} -n {} --yes'.format(rg, name))
        self.cmd('batch account delete -g {} -n {} --yes'.format(rg, self.byos_account_name))
        self.cmd('batch account list -g {}'.format(rg), checks=NoneCheck())

        self.cmd('batch location quotas show -l {}'.format(loc),
                 checks=[JMESPathCheck('accountQuota', 1)])


class BatchMgmtApplicationScenarioTest(ResourceGroupVCRTestBase):

    def set_up(self):
        super(BatchMgmtApplicationScenarioTest, self).set_up()

        rg = self.resource_group
        sname = self.storage_account_name
        name = self.account_name
        loc = self.location

        # test create account with default set
        result = self.cmd('storage account create -g {} -n {} -l {} --sku Standard_LRS'.
                          format(rg, sname, loc), checks=[
                              JMESPathCheck('name', sname),
                              JMESPathCheck('location', loc),
                              JMESPathCheck('resourceGroup', rg)
                          ])

        self.cmd('batch account create -g {} -n {} -l {} --storage-account {}'.
                 format(rg, name, loc, result['id']), checks=[
                     JMESPathCheck('name', name),
                     JMESPathCheck('location', loc),
                     JMESPathCheck('resourceGroup', rg)
                 ])

    def tear_down(self):
        rg = self.resource_group
        sname = self.storage_account_name
        name = self.account_name
        self.cmd('storage account delete -g {} -n {} --yes'.format(rg, sname))
        self.cmd('batch account delete -g {} -n {} --yes'.format(rg, name))

    def __init__(self, test_method):
        super(BatchMgmtApplicationScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'vcr_resource_group'
        self.account_name = 'clibatchtest7'
        self.location = 'brazilsouth'
        self.storage_account_name = 'clibatchteststorage7'
        self.application_name = 'testapp'
        self.application_package_name = '1.0'
        _, self.package_file_name = tempfile.mkstemp()

    def test_batch_application_mgmt(self):
        self.execute()

    def body(self):
        with open(self.package_file_name, 'w') as f:
            f.write('storage blob test sample file')

        rg = self.resource_group
        name = self.account_name
        aname = self.application_name
        ver = self.application_package_name
        # test create application with default set
        self.cmd('batch application create -g {} -n {} --application-id {} --allow-updates'.
                 format(rg, name, aname), checks=[
                     JMESPathCheck('id', aname),
                     JMESPathCheck('allowUpdates', True)
                 ])

        self.cmd('batch application list -g {} -n {}'.format(rg, name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].id', aname),
        ])

        self.cmd('batch application package create -g {} -n {} --application-id {}'
                 ' --version {} --package-file "{}"'.
                 format(rg, name, aname, ver, self.package_file_name), checks=[
                     JMESPathCheck('id', aname),
                     JMESPathCheck('storageUrl != null', True),
                     JMESPathCheck('version', ver),
                     JMESPathCheck('state', 'active')
                 ])

        self.cmd('batch application package activate -g {} -n {} --application-id {}'
                 ' --version {} --format zip'.format(rg, name, aname, ver))

        self.cmd('batch application package show -g {} -n {} --application-id {} --version {}'.
                 format(rg, name, aname, ver), checks=[
                     JMESPathCheck('id', aname),
                     JMESPathCheck('format', 'zip'),
                     JMESPathCheck('version', ver),
                     JMESPathCheck('state', 'active')
                 ])

        self.cmd('batch application set -g {} -n {} --application-id {} --default-version {}'.format(rg, name, aname, ver))  # pylint: disable=line-too-long

        self.cmd('batch application show -g {} -n {} --application-id {}'.format(rg, name, aname),
                 checks=[JMESPathCheck('id', aname),
                         JMESPathCheck('defaultVersion', ver),
                         JMESPathCheck('packages[0].format', 'zip'),
                         JMESPathCheck('packages[0].state', 'active')])

        # test batch applcation delete
        self.cmd('batch application package delete -g {} -n {} --application-id {} --version {} --yes'.  # pylint: disable=line-too-long
                 format(rg, name, aname, ver))
        self.cmd('batch application delete -g {} -n {} --application-id {} --yes'.
                 format(rg, name, aname))
        self.cmd('batch application list -g {} -n {}'.format(rg, name), checks=NoneCheck())
