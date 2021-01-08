# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

LOCATION = "eastus2euap"


class AzureNetAppFilesVaultServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name, volume_only=False):
        vnet_name = "cli-vnet-lefr-02"
        subnet_name = "cli-subnet-lefr-02"

        if not volume_only:
            # create vnet, account and pool
            self.setup_vnet(vnet_name, subnet_name)
            self.cmd("netappfiles account create -g {rg} -a '%s' -l %s" %
                     (account_name, LOCATION)).get_output_in_json()
            self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4" %
                     (account_name, pool_name, LOCATION)).get_output_in_json()

        # create volume
        return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s --vnet %s --subnet %s "
                        "--file-path %s --usage-threshold 100" %
                        (account_name, pool_name, volume_name, LOCATION, vnet_name, subnet_name, volume_name)) \
            .get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_vault_')
    def test_list_vault(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume_name)

        vault_list = self.cmd("az netappfiles vault list -g {rg} -a %s" % account_name).get_output_in_json()
        assert len(vault_list) == 1
