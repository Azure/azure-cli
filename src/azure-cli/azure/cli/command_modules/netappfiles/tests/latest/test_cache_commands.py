# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

LOCATION = "eastus"
VNET_LOCATION = "eastus"
POOL_DEFAULT = "--service-level Premium --size 4"

# No tidy up of tests required. The resource group is automatically removed

# Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed

# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer


class AzureNetAppFilesCacheServiceScenarioTest(ScenarioTest):
    def setup_vnets(self, cache_vnet_name, cache_subnet_name, peering_vnet_name, peering_subnet_name):
        # cache subnet and peering subnet must reside on different VNets
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (cache_vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (cache_subnet_name, cache_vnet_name))
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.6.0.0/16" %
                 (peering_vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.6.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (peering_subnet_name, peering_vnet_name))

    def create_cache(self, account_name, pool_name, cache_name, cache_vnet_name=None, peering_vnet_name=None,
                     cache_only=False):
        if cache_vnet_name is None:
            cache_vnet_name = self.create_random_name(prefix='cli-vnet-cache', length=24)
        if peering_vnet_name is None:
            peering_vnet_name = self.create_random_name(prefix='cli-vnet-peer', length=24)
        cache_subnet_name = "cacheSubnet"
        peering_subnet_name = "peeringSubnet"

        if not cache_only:
            # create vnets, account and pool
            self.setup_vnets(cache_vnet_name, cache_subnet_name, peering_vnet_name, peering_subnet_name)
            self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))
            self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s" %
                     (account_name, pool_name, LOCATION, POOL_DEFAULT))

        # build subnet resource ids - each on its own VNet
        cache_subnet_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}".format(
            sub=self.get_subscription_id(), rg='{rg}', vnet=cache_vnet_name, subnet=cache_subnet_name)
        peering_subnet_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}".format(
            sub=self.get_subscription_id(), rg='{rg}', vnet=peering_vnet_name, subnet=peering_subnet_name)

        file_path = self.create_random_name(prefix='filepath', length=16)

        # create cache
        return self.cmd("az netappfiles cache create -g {rg} -a %s -p %s -n %s -l %s "
                        "--protocol-types NFSv3 "
                        "--file-path %s --size 107374182400 "
                        "--encryption-key-source Microsoft.NetApp "
                        "--cache-subnet-resource-id %s "
                        "--peering-subnet-resource-id %s "
                        "--peer-cluster-name cluster1 "
                        "--peer-addresses 192.0.2.10 192.0.2.11 "
                        "--peer-vserver-name vserver1 "
                        "--peer-volume-name originvol1" %
                        (account_name, pool_name, cache_name, LOCATION,
                         file_path, cache_subnet_id, peering_subnet_id)).get_output_in_json()

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_cache(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        cache = self.create_cache(account_name, pool_name, cache_name)
        assert cache['name'] == account_name + '/' + pool_name + '/' + cache_name
        assert cache['size'] == 107374182400
        assert cache['encryptionKeySource'] == 'Microsoft.NetApp'
        assert cache['originClusterInformation']['peerClusterName'] == 'cluster1'
        assert cache['originClusterInformation']['peerVserverName'] == 'vserver1'
        assert cache['originClusterInformation']['peerVolumeName'] == 'originvol1'
        assert len(cache['originClusterInformation']['peerAddresses']) == 2

        # verify cache exists in list
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 1

        # delete cache
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name))

        # verify deletion
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_cache_with_wait(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # delete with --no-wait then use wait --deleted
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes --no-wait" %
                 (account_name, pool_name, cache_name))
        self.cmd("az netappfiles cache wait -g {rg} -a %s -p %s -n %s --deleted" %
                 (account_name, pool_name, cache_name))

        # verify deletion
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_list_caches(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name_1 = self.create_random_name(prefix='cli-cache-', length=24)
        cache_name_2 = self.create_random_name(prefix='cli-cache-', length=24)

        # create first cache (also creates vnets, account, pool)
        cache_vnet_name = self.create_random_name(prefix='cli-vnet-cache', length=24)
        peering_vnet_name = self.create_random_name(prefix='cli-vnet-peer', length=24)
        self.create_cache(account_name, pool_name, cache_name_1, cache_vnet_name=cache_vnet_name,
                          peering_vnet_name=peering_vnet_name)

        # create second cache in the same pool (cache_only=True reuses existing infra)
        self.create_cache(account_name, pool_name, cache_name_2, cache_vnet_name=cache_vnet_name,
                          peering_vnet_name=peering_vnet_name, cache_only=True)

        # list and verify count
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 2

        # delete both caches
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name_1))
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name_2))

        # verify all deleted
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_get_cache_by_name(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # get cache by name
        cache = self.cmd("az netappfiles cache show -g {rg} -a %s -p %s -n %s" %
                         (account_name, pool_name, cache_name)).get_output_in_json()
        assert cache['name'] == account_name + '/' + pool_name + '/' + cache_name

        # get cache by resource id
        cache_from_id = self.cmd("az netappfiles cache show --ids %s" % cache['id']).get_output_in_json()
        assert cache_from_id['name'] == account_name + '/' + pool_name + '/' + cache_name

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_update_cache(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # update cache tags and size
        tags = "Tag1=Value1 Tag2=Value2"
        new_size = 214748364800
        self.cmd("az netappfiles cache update -g {rg} -a %s -p %s -n %s --tags %s --size %s" %
                 (account_name, pool_name, cache_name, tags, new_size))

        # verify update
        cache = self.cmd("az netappfiles cache show -g {rg} -a %s -p %s -n %s" %
                         (account_name, pool_name, cache_name)).get_output_in_json()
        assert cache['tags']['Tag1'] == 'Value1'
        assert cache['tags']['Tag2'] == 'Value2'
        assert cache['properties']['size'] == new_size

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_cache_pool_change(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        pool_name_2 = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # create second pool
        pool2 = self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s" %
                         (account_name, pool_name_2, LOCATION, POOL_DEFAULT)).get_output_in_json()

        # move cache to the second pool
        self.cmd("az netappfiles cache pool-change -g {rg} -a %s -p %s -c %s --new-pool-resource-id %s" %
                 (account_name, pool_name, cache_name, pool2['id']))

        # verify cache is now in pool2
        cache_list_pool1 = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                                    (account_name, pool_name)).get_output_in_json()
        assert len(cache_list_pool1) == 0

        cache_list_pool2 = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                                    (account_name, pool_name_2)).get_output_in_json()
        assert len(cache_list_pool2) == 1

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_cache_list_peering_passphrase(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # list peering passphrase
        result = self.cmd("az netappfiles cache list-peering-passphrase -g {rg} -a %s -p %s -c %s" %
                          (account_name, pool_name, cache_name)).get_output_in_json()
        assert result is not None

    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_cache_reset_smb_password(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # reset smb password - verify the command completes without error
        self.cmd("az netappfiles cache reset-smb-password -g {rg} -a %s -p %s -c %s" %
                 (account_name, pool_name, cache_name))
