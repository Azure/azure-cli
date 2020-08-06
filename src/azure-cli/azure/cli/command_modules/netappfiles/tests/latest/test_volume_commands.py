# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time

POOL_DEFAULT = "--service-level 'Premium' --size 4"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 100"
RG_LOCATION = "westus2"
ANF_LOCATION = "westus2stage"
DP_RG_LOCATION = "southcentralus"
DP_ANF_LOCATION = "southcentralusstage"
GIB_SCALE = 1024 * 1024 * 1024

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesVolumeServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name, ip_pre, location):
        self.cmd("az network vnet create -n %s --resource-group %s -l %s --address-prefix %s/16" % (vnet_name, rg, location, ip_pre))
        self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '%s/24' --delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name, ip_pre))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None, volume_name2=None, protocols=None, pool_payload=POOL_DEFAULT, volume_payload=VOLUME_DEFAULT):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name1  # creation_token
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        tag = "--tags %s" % tags if tags is not None else ""
        protocol_types = "--protocol-types %s" % protocols if protocols is not None else ""

        self.setup_vnet(rg, vnet_name, subnet_name, '10.0.0.0', RG_LOCATION)
        self.cmd("az netappfiles account create -g %s -a '%s' -l %s" % (rg, account_name, ANF_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s %s" % (rg, account_name, pool_name, ANF_LOCATION, pool_payload, tag)).get_output_in_json()
        volume1 = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s %s %s" % (rg, account_name, pool_name, volume_name1, ANF_LOCATION, volume_payload, file_path, vnet_name, subnet_name, protocol_types, tag)).get_output_in_json()

        if volume_name2:
            file_path = volume_name2
            self.cmd("az netappfiles volume create -g %s -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s --subnet %s --tags %s" % (rg, account_name, pool_name, volume_name2, ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_name, tags)).get_output_in_json()

        return volume1

    def wait_for_replication_status(self, target_state, rg_r, account_name_r, pool_name_r, volume_name_r):
        # python isn't good at do-while loops but loop until we get the target state
        attempts = 0
        replication_status = self.cmd("az netappfiles volume replication status -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r)).get_output_in_json()

        while attempts < 10:
            attempts += 1
            replication_status = self.cmd("az netappfiles volume replication status -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r)).get_output_in_json()
            if(replication_status['mirrorState'] == target_state):
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

        assert replication_status['mirrorState'] == target_state

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_create_delete_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1 Tag2=Value2"

        protocol_types = "NFSv3"
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', tags=tags, protocols=protocol_types)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['tags']['Tag1'] == 'Value1'
        assert volume['tags']['Tag2'] == 'Value2'
        # default export policy still present
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == '0.0.0.0/0'
        assert not volume['exportPolicy']['rules'][0]['cifs']
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == 1
        # check a mount target is present
        assert len(volume['mountTargets']) == 1
        # specified protocol type
        assert len(volume['protocolTypes']) == 1
        assert volume['protocolTypes'][0] == 'NFSv3'
        # replication
        assert volume['volumeType'] is None
        assert volume['dataProtection'] is None

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} --account-name %s --pool-name %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

        self.cmd("az netappfiles volume delete --resource-group {rg} --account-name %s --pool-name %s --volume-name %s" % (account_name, pool_name, volume_name))
        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a %s -p %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_create_volume_with_subnet_in_different_rg(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name  # creation_token
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)

        subnet_rg = self.create_random_name(prefix='cli-rg-subnet', length=24)
        subs_id = self.current_subscription()
        self.cmd("az group create -n %s --subscription %s -l %s" % (subnet_rg, subs_id, RG_LOCATION)).get_output_in_json()

        rg = '{rg}'
        self.setup_vnet(subnet_rg, vnet_name, subnet_name, '10.0.0.0', RG_LOCATION)
        self.cmd("az netappfiles account create -g %s -a %s -l %s" % (rg, account_name, ANF_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % (rg, account_name, pool_name, ANF_LOCATION, POOL_DEFAULT)).get_output_in_json()

        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, subnet_rg, vnet_name, subnet_name)

        volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s" % (rg, account_name, pool_name, volume_name, ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_id)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        self.cmd("az netappfiles volume delete --resource-group %s --account-name %s --pool-name %s --volume-name %s" % (rg, account_name, pool_name, volume_name))
        self.cmd("az group delete --yes -n %s" % (subnet_rg))

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    @ResourceGroupPreparer(name_prefix='cli_netappf_test_volume2_', parameter_name='replication_resourcegroup')
    def test_perform_replication(self, resource_group, replication_resourcegroup):
        # create source volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        account_name_r = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        pool_name_r = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        volume_name_r = self.create_random_name(prefix='cli-vol-', length=24)
        rg = '{rg}'

        src_volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert src_volume['id'] is not None

        # create destination volume in other region/rg and with its own vnet
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name_r  # creation_token
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        # rg_r = self.create_random_name(prefix='cli-rg-', length=24)
        rg_r = replication_resourcegroup
        subs_id = self.current_subscription()
        #  self.cmd("az group create -n %s --subscription %s -l %s" % (rg_r, subs_id, DP_RG_LOCATION)).get_output_in_json()

        self.setup_vnet(rg_r, vnet_name, subnet_name, '10.1.0.0', DP_RG_LOCATION)
        self.cmd("az netappfiles account create -g %s -a %s -l %s" % (rg_r, account_name_r, DP_ANF_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % (rg_r, account_name_r, pool_name_r, DP_ANF_LOCATION, POOL_DEFAULT)).get_output_in_json()

        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, rg_r, vnet_name, subnet_name)

        # volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s" % (rg_r, account_name_r, pool_name_r, volume_name_r, DP_ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_id)).get_output_in_json()

        dst_volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s --volume-type %s --endpoint-type %s --replication-schedule %s --remote-volume-resource-id %s" % (rg_r, account_name_r, pool_name_r, volume_name_r, DP_ANF_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_id, "DataProtection", "dst", "_10minutely", src_volume['id'])).get_output_in_json()
        assert dst_volume['dataProtection'] is not None
        assert dst_volume['id'] is not None
        time.sleep(2)

        # approve
        self.cmd("az netappfiles volume replication approve -g %s -a %s -p %s -v %s --remote-volume-resource-id %s" % (rg, account_name, pool_name, volume_name, dst_volume['id']))
        self.wait_for_replication_status("Mirrored", rg_r, account_name_r, pool_name_r, volume_name_r)

        # break
        self.cmd("az netappfiles volume replication suspend -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r))
        self.wait_for_replication_status("Broken", rg_r, account_name_r, pool_name_r, volume_name_r)

        # resume
        self.cmd("az netappfiles volume replication resume -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r))
        self.wait_for_replication_status("Mirrored", rg_r, account_name_r, pool_name_r, volume_name_r)

        # break
        self.cmd("az netappfiles volume replication suspend -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r))
        self.wait_for_replication_status("Broken", rg_r, account_name_r, pool_name_r, volume_name_r)

        # delete
        self.cmd("az netappfiles volume replication remove -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r))
        time.sleep(2)

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_list_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name1 = self.create_random_name(prefix='cli-vol-', length=24)
        volume_name2 = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1"

        self.create_volume(account_name, pool_name, volume_name1, '{rg}', tags=tags, volume_name2=volume_name2)

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 2

        self.cmd("az netappfiles volume delete -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name1))
        volume_list = self.cmd("netappfiles volume list -g {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_get_volume_by_name(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag2=Value1"

        protocol_types = "NFSv4.1"
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', tags=tags, protocols=protocol_types)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # specified protocol type
        assert len(volume['protocolTypes']) == 1
        assert volume['protocolTypes'][0] == 'NFSv4.1'
        assert len(volume['exportPolicy']['rules']) == 1
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == 1
        assert volume['exportPolicy']['rules'][0]['nfsv41']
        assert not volume['exportPolicy']['rules'][0]['nfsv3']

        volume = self.cmd("az netappfiles volume show --resource-group {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['tags']['Tag2'] == 'Value1'

        volume_from_id = self.cmd("az netappfiles volume show --ids %s" % volume['id']).get_output_in_json()
        assert volume_from_id['name'] == account_name + '/' + pool_name + '/' + volume_name

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_update_volume(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value2"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # default protocol type
        assert len(volume['protocolTypes']) == 1
        assert volume['protocolTypes'][0] == 'NFSv3'
        assert volume['usageThreshold'] == 100 * GIB_SCALE

        volume = self.cmd("az netappfiles volume update --resource-group {rg} -a %s -p %s -v %s --tags %s --usage-threshold 200" % (account_name, pool_name, volume_name, tags)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['serviceLevel'] == "Premium"  # unchanged
        assert volume['usageThreshold'] == 200 * GIB_SCALE
        assert volume['tags']['Tag1'] == 'Value2'
        # default export policy still present
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == '0.0.0.0/0'
        assert not volume['exportPolicy']['rules'][0]['cifs']
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == 1

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_export_policy(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # now add an export policy
        # there is already one default rule present
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][0]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][0]['ruleIndex'] == 3
        assert vol_with_export_policy['exportPolicy']['rules'][0]['cifs'] is False

        # and add another export policy
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.4.0/24' --rule-index 2 --unix-read-only true --unix-read-write false --cifs true --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][1]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][0]['allowedClients'] == '1.2.4.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][0]['cifs'] is True
        assert len(vol_with_export_policy['exportPolicy']['rules']) == 3

        # list the policies
        export_policy = self.cmd("netappfiles volume export-policy list -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(export_policy['rules']) == 3

        # and remove one
        vol_with_export_policy = self.cmd("netappfiles volume export-policy remove -g {rg} -a %s -p %s -v %s --rule-index 2" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert len(vol_with_export_policy['exportPolicy']['rules']) == 2

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_')
    def test_export_policy_non_default(self):
        # tests that adding export policy works with non-default service level/usage threshold
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool_payload = "--service-level 'Standard' --size 8"
        volume_payload = "--service-level 'Standard' --usage-threshold 200"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', pool_payload=pool_payload, volume_payload=volume_payload)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # check the specified volume properties
        assert volume['usageThreshold'] == 200 * GIB_SCALE
        assert volume['serviceLevel'] == "Standard"

        # now add an export policy
        # there is already one default rule present
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][0]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][0]['ruleIndex'] == 3
        assert vol_with_export_policy['exportPolicy']['rules'][0]['cifs'] is False
        # and recheck the other properties are unchanged
        assert volume['usageThreshold'] == 200 * GIB_SCALE
        assert volume['serviceLevel'] == "Standard"
