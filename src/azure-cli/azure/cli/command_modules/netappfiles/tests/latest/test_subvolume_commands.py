# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest

LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"


@unittest.skip("Service has been hardened and we need to check if this is testable")
class AzureNetAppFilesSubvolumeServiceScenarioTest(ScenarioTest):
    def create_volume(self, volume_only=False):
        if not volume_only:
            # create vnet, account and pool
            self.cmd("az network vnet create -n {vnet} -g {rg} -l {vnet_loc} --address-prefix 10.5.0.0/16")
            self.cmd("az network vnet subnet create -n {subnet} --vnet-name {vnet} --address-prefixes '10.5.0.0/24' "
                     "--delegations 'Microsoft.Netapp/volumes' -g {rg}")
            self.cmd("netappfiles account create -g {rg} -a {acc_name} -l {loc}")
            self.cmd("netappfiles pool create -g {rg} -a {acc_name} -p {pool_name} -l {loc} --service-level 'Premium' "
                     "--size 4")

        # create volume
        return self.cmd("netappfiles volume create -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} -l {loc} "
                        "--vnet {vnet} --subnet {subnet} --file-path {vol_name} --usage-threshold 100 "
                        "--enable-subvolumes {enable_subvolumes}")

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_subvolume_crud_', additional_tags={'owner': 'cli_test'})
    def test_subvolume_crud(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'sub_vol_name': self.create_random_name(prefix='cli-sub-vol-', length=24),
            'path': "/sub_vol_1.txt",
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION,
            'enable_subvolumes': 'Enabled'
        })
        self.create_volume()

        # create
        self.cmd("az netappfiles subvolume create -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name} --path {path}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name}'),
            self.check('path', '{path}')])

        # update
        self.kwargs.update({
            'path': "/sub_vol_update.txt"
        })
        self.cmd("az netappfiles subvolume update -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name} --path {path}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name}'),
            self.check('path', '{path}')])

        # get
        self.cmd("az netappfiles subvolume show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name}'),
            self.check('path', '{path}')])

        # delete
        self.cmd("az netappfiles subvolume delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name} -y")
        self.cmd("az netappfiles subvolume list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check('length(@)', 0)])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_subvolume_list_', additional_tags={'owner': 'cli_test'})
    def test_subvolume_list(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'sub_vol_name1': self.create_random_name(prefix='cli-sub-vol-', length=24),
            'sub_vol_name2': self.create_random_name(prefix='cli-sub-vol-', length=24),
            'path1': "/sub_vol_1.txt",
            'path2': "/sub_vol_2.txt",
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION,
            'enable_subvolumes': 'Enabled'
        })
        self.create_volume()

        # create
        self.cmd("az netappfiles subvolume create -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name1} --path {path1}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name1}'),
            self.check('path', '{path1}')])

        # list
        self.cmd("az netappfiles subvolume list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check('length(@)', 1)])

        # create
        self.cmd("az netappfiles subvolume create -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name2} --path {path2}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name2}'),
            self.check('path', '{path2}')])

        # list
        self.cmd("az netappfiles subvolume list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check('length(@)', 2)])

        # delete
        self.cmd("az netappfiles subvolume delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name1} -y")

        # list
        self.cmd("az netappfiles subvolume list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check('length(@)', 1)])

        # delete
        self.cmd("az netappfiles subvolume delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name2} -y")

        # list
        self.cmd("az netappfiles subvolume list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check('length(@)', 0)])

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_subvolume_metadata_', additional_tags={'owner': 'cli_test'})
    def test_subvolume_get_metadata(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'sub_vol_name': self.create_random_name(prefix='cli-sub-vol-', length=24),
            'path': "/sub_vol_1.txt",
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION,
            'enable_subvolumes': 'Enabled'
        })
        self.create_volume()

        # create
        self.cmd("az netappfiles subvolume create -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name} --path {path}", checks=[
            self.check('name', '{acc_name}' + '/' + '{pool_name}' + '/' + '{vol_name}' + '/' + '{sub_vol_name}'),
            self.check('path', '{path}')])

        # get metadata
        self.cmd("az netappfiles subvolume metadata show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name}", checks=[
            self.check('path', '{path}')])

        self.cmd("az netappfiles subvolume delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} "
                 "--subvolume-name {sub_vol_name} -y")
        