# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "westcentralus"
VNET_LOCATION = "westcentralus"


class AzureNetAppFilesVolumeQuotaRuleServiceScenarioTest(ScenarioTest):
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

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_quota_rule_', additional_tags={'owner': 'cli_test'})
    def test_create_volume_quota_rule(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'qr_name': self.create_random_name(prefix='cli-qr-', length=24),
            'size': 100006,
            'size2': 1000016,
            'type': "DefaultGroupQuota",
            'target': "" ,
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION
        })
        self.create_volume()

        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check("length(@)", 0)
        ])

        # Create quota rule
        self.cmd("az netappfiles volume quota-rule create -g {rg} -a {acc_name} -p {pool_name} -l {loc} -v {vol_name} --quota-rule-name {qr_name} --quota-size {size} --quota-type {type} --quota-target '' " )
        # List quota rules
        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check("length(@)", 1)
        ])
        # Get quota rule
        self.cmd("az netappfiles volume quota-rule show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name}", checks=[            
            self.check('quotaSizeInKiBs', '{size}')
        ])
        # Update quota rule
        self.cmd("az netappfiles volume quota-rule update -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name} --quota-size {size2} --quota-type {type}")
        # Get quota rule
        self.cmd("az netappfiles volume quota-rule show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name}", checks=[            
            self.check('quotaSizeInKiBs', '{size2}'),
            self.check('quotaType', '{type}')
        ])
        # Delete quota rule
        self.cmd("az netappfiles volume quota-rule delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name} -y")

        # List quota rule - make sure it was deleted
        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} ", checks=[
            self.check("length(@)", 0)
        ])


    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_quota_rule_', additional_tags={'owner': 'cli_test'})
    def test_volume_quota_rule_list(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix='cli-acc-', length=24),
            'pool_name': self.create_random_name(prefix='cli-pool-', length=24),
            'vol_name': self.create_random_name(prefix='cli-vol-', length=24),
            'qr_name': self.create_random_name(prefix='cli-qr-', length=24),
            'qr_name_user_rule': self.create_random_name(prefix='cli-qr-', length=24),
            'size': 100006,
            'size_user_rule': 1000016,
            'type': "DefaultGroupQuota",
            'type_user': "DefaultUserQuota",
            'target': "" ,
            'vnet': self.create_random_name(prefix='cli-vnet-', length=24),
            'subnet': self.create_random_name(prefix='cli-subnet-', length=24),
            'vnet_loc': VNET_LOCATION
        })
        self.create_volume()

        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check("length(@)", 0)
        ])

        # Create quota rule
        self.cmd("az netappfiles volume quota-rule create -g {rg} -a {acc_name} -p {pool_name} -l {loc} -v {vol_name} --quota-rule-name {qr_name} --quota-size {size} --quota-type {type} --quota-target '' " )
        # List quota rules
        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check("length(@)", 1)
        ])
        # Get quota rule
        self.cmd("az netappfiles volume quota-rule show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name}", checks=[            
            self.check('quotaSizeInKiBs', '{size}')
        ])
        # Create another quota rule
        self.cmd("az netappfiles volume quota-rule create -g {rg} -a {acc_name} -p {pool_name} -l {loc} -v {vol_name} --quota-rule-name {qr_name_user_rule} --quota-size {size} --quota-type {type_user} --quota-target '' " )

        # List quota rules
        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}", checks=[
            self.check("length(@)", 2)
        ])

        # Delete quota rule
        self.cmd("az netappfiles volume quota-rule delete -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} --quota-rule-name {qr_name} -y")

        # List quota rule - make sure it was deleted
        self.cmd("az netappfiles volume quota-rule list -g {rg} -a {acc_name} -p {pool_name} -v {vol_name} ", checks=[
            self.check("length(@)", 1)
        ])