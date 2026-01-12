# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

# POOL_DEFAULT = "--service-level 'Premium' --size 4398046511104"
POOL_DEFAULT = "--service-level 'Premium' --size 4"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 107374182400"
RG_LOCATION = "eastus"
# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesBackupvaultServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name, ip_pre):
        self.cmd("az network vnet create -n %s --resource-group %s -l %s --address-prefix %s/16" % (vnet_name, rg, RG_LOCATION, ip_pre))
        self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '%s/24' --delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name, ip_pre))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None, volume_name2=None):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        creation_token = volume_name1
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (self.current_subscription(), rg, vnet_name, subnet_name)
        tag = "--tags '%s'" % tags if tags is not None else ""

        self.setup_vnet(rg, vnet_name, subnet_name, '10.12.0.0')
        self.cmd("az netappfiles account create -g %s -a '%s' -l %s" % (rg, account_name,RG_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s %s" % (rg, account_name, pool_name,RG_LOCATION, POOL_DEFAULT, tag)).get_output_in_json()
        volume1 = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --creation-token %s --vnet %s --subnet %s %s" % (rg, account_name, pool_name, volume_name1, RG_LOCATION, VOLUME_DEFAULT, creation_token,vnet_name, subnet_id, tag)).get_output_in_json()

        if volume_name2:
            creation_token = volume_name2
            self.cmd("az netappfiles volume create -g %s -a %s -p %s -v %s -l %s %s --creation-token %s --subnet-id %s --tags '%s' --vnet %s" % (rg, account_name, pool_name, volume_name2, RG_LOCATION, VOLUME_DEFAULT, creation_token, subnet_id, tags, vnet_name)).get_output_in_json()

        return volume1

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_create_delete_backupvault(self,resource_group):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)        
        tags = "Tag1=Value1 Tag2=Value2"
        self.kwargs.update({
            'account_name': account_name,            
            'vault_name': vault_name
        })
        self.cmd(f"az netappfiles account create -g {resource_group} -a {account_name} -l {RG_LOCATION}")
        
        backupvault = self.cmd(f"az netappfiles account backup-vault create -g {resource_group} -a {account_name} -n {vault_name} -l {RG_LOCATION} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name
        #assert volume['tags']['Tag1'] == 'Value1'
        #assert volume['tags']['Tag2'] == 'Value2'
        
        backupvault_list = self.cmd(f"az netappfiles account backup-vault list --resource-group {resource_group} -a {account_name}").get_output_in_json()
        assert len(backupvault_list) == 1

        self.cmd(f"az netappfiles account backup-vault delete --resource-group {resource_group} -a {account_name} -n {vault_name} -y")
        backupvault_list = self.cmd(f"az netappfiles account backup-vault list --resource-group {resource_group} -a {account_name}").get_output_in_json()
        assert len(backupvault_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_get_backupvault_by_name(self, resource_group):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,            
            'vault_name': vault_name
        })
        tags = "Tag1=Value1 Tag2=Value2"
        self.cmd(f"az netappfiles account create -g {resource_group} -a {account_name} -l {RG_LOCATION}")
        
        backupvault = self.cmd(f"az netappfiles account backup-vault create -g {resource_group} -a {account_name} -n {vault_name} -l {RG_LOCATION} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name

        backupvault = self.cmd(f"az netappfiles account backup-vault show --resource-group {resource_group} -a {account_name} -n {vault_name}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name
        assert backupvault['tags']['Tag2'] == 'Value2'
        
        backupvault_from_id = self.cmd(f"az netappfiles account backup-vault show --ids {backupvault['id']} ").get_output_in_json()
        assert backupvault_from_id['name'] == account_name + '/' + vault_name

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_list_backupvault(self, resource_group):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        vault_name2 = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,            
            'vault_name': vault_name,
            'vault_name2': vault_name2
        })
        tags = "Tag1=Value1 Tag2=Value2"
        self.cmd(f"az netappfiles account create -g {resource_group} -a {account_name} -l {RG_LOCATION}")
        
        backupvault = self.cmd(f"az netappfiles account backup-vault create -g {resource_group} -a {account_name} -n {vault_name} -l {RG_LOCATION} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name

        backupvault = self.cmd(f"az netappfiles account backup-vault show --resource-group {resource_group} -a {account_name} -n {vault_name}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name
        assert backupvault['tags']['Tag2'] == 'Value2'
        
        backupvaults = self.cmd(f"az netappfiles account backup-vault list --resource-group {resource_group} -a {account_name} ").get_output_in_json()
        assert len(backupvaults) == 1

        backupvault = self.cmd(f"az netappfiles account backup-vault create -g {resource_group} -a {account_name} -n {vault_name2} -l {RG_LOCATION} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name2        
        backupvaults = self.cmd(f"az netappfiles account backup-vault list --resource-group {resource_group} -a {account_name} ").get_output_in_json()
        assert len(backupvaults) == 2
                

    @ResourceGroupPreparer(name_prefix='cli_tests_rg')
    def test_update_backupvault(self, resource_group):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        vault_name = self.create_random_name(prefix='cli-backupvault-', length=24)
        self.kwargs.update({
            'account_name': account_name,            
            'vault_name': vault_name
        })
        tags = "Tag1=Value1 Tag2=Value2"
        self.cmd(f"az netappfiles account create -g {resource_group} -a {account_name} -l {RG_LOCATION}")
        
        backupvault = self.cmd(f"az netappfiles account backup-vault create -g {resource_group} -a {account_name} -n {vault_name} -l {RG_LOCATION} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name
        
        tags = "Tag1=Value1 Tag2=Value2Updated"
        backupvault = self.cmd(f"az netappfiles account backup-vault update -g {resource_group} -a {account_name} -n {vault_name} --tags {tags}").get_output_in_json()
        assert backupvault['name'] == account_name + '/' + vault_name
        assert backupvault['tags']['Tag2'] == 'Value2Updated'
