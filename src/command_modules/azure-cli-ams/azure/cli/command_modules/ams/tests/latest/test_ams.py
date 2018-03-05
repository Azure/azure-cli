# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from knack.util import CLIError

class AmsTests(ScenarioTest):
    
    @ResourceGroupPreparer()
    def test_ams_list(self, resource_group):
        list = self.cmd('az ams list -g {}'.format(resource_group)).get_output_in_json()
        assert len(list) > 0

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_create_show(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}',
                checks=[self.check('name', '{amsname}'),
                        self.check('location', 'West US 2')])

        self.cmd('az ams show -n {amsname} -g {rg}',
                 checks=[self.check('name', '{amsname}'),
                         self.check('resourceGroup', '{rg}')])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_storage_add_remove(self, resource_group, storage_account_for_create, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}',
                checks=[self.check('name', '{amsname}'),
                        self.check('location', 'West US 2')])

        self.kwargs.update({
            'storageAccount': storage_account_for_update
        })

        self.cmd('az ams storage add -n {amsname} -g {rg} --storage-account {storageAccount}',
                checks=[self.check('name', '{amsname}'),
                        self.check('resourceGroup', '{rg}')])

        self.cmd('az ams storage remove -n {amsname} -g {rg} --storage-account {storageAccount}',
                 checks=[self.check('name', '{amsname}'),
                         self.check('resourceGroup', '{rg}')])