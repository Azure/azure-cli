# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"


class AzureNetAppFilesVaultServiceScenarioTest(ScenarioTest):
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
                        "--vnet {vnet} --subnet {subnet} --file-path {vol_name} --usage-threshold 100")

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_vault_list_', additional_tags={'owner': 'cli_test'})
    def test_list_vault(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION
        })
        self.create_volume()

        self.cmd("az netappfiles vault list -g {rg} -a {acc_name}", checks=[
            self.check("length(@)", 1)
        ])
