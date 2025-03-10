# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import ValidationError
from azure.core.exceptions import HttpResponseError
from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test
import time
import unittest

POOL_DEFAULT = "--service-level 'Premium' --size 4"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 100"

# RG_LOCATION = "southcentralusstage"
# DP_RG_LOCATION = "eastus2euap"
# VNET_LOCATION = "southcentralus"

RG_LOCATION = "eastus"
DP_RG_LOCATION = "westus"
VNET_LOCATION = "eastus"

# RG_LOCATION = "uksouth"
# DP_RG_LOCATION = "ukwest"
# VNET_LOCATION = "uksouth"

GIB_SCALE = 1024 * 1024 * 1024

# No tidy up of tests required. The resource group is automatically removed


class AzureNetAppFilesVolumeServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, rg, vnet_name, subnet_name, ip_pre, location):
        self.cmd("az network vnet create -n %s --resource-group %s -l %s --address-prefix %s/16" % (vnet_name, rg, location, ip_pre))
        self.cmd("az network vnet subnet create -n %s -g %s --vnet-name %s --address-prefixes '%s/24' --delegations 'Microsoft.Netapp/volumes'" % (subnet_name, rg, vnet_name, ip_pre))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name1, rg, tags=None, volume_name2=None, protocols=None,
                      pool_payload=POOL_DEFAULT, volume_payload=VOLUME_DEFAULT, rule_index=1, allowed_clients="0.0.0.0/0"):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        file_path = volume_name1  # creation_token
        protocol_types = "--protocol-types %s" % protocols if protocols is not None else ""
        tag = "--tags %s" % tags if tags is not None else ""

        self.prepare_for_volume_creation(rg, account_name, pool_name, vnet_name, subnet_name, pool_payload, tags)

        volume1 = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s "
                           "--volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s %s %s --rule-index %s "
                           "--allowed-clients %s" %
                           (rg, account_name, pool_name, volume_name1, RG_LOCATION, volume_payload, file_path,
                            vnet_name, subnet_name, protocol_types, tag, rule_index, allowed_clients)).get_output_in_json()

        if volume_name2:
            file_path = volume_name2
            self.cmd("az netappfiles volume create -g %s -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s --subnet %s --tags %s" % (rg, account_name, pool_name, volume_name2, RG_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_name, tags)).get_output_in_json()

        return volume1

    def prepare_for_volume_creation(self, rg, account_name, pool_name, vnet_name, subnet_name,
                                    pool_payload=POOL_DEFAULT, tags=None):
        tag = "--tags %s" % tags if tags is not None else ""
        self.setup_vnet(rg, vnet_name, subnet_name, '10.0.0.0', VNET_LOCATION)
        self.cmd("az netappfiles account create -g %s -a '%s' -l %s" %
                 (rg, account_name, RG_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s %s" %
                 (rg, account_name, pool_name, RG_LOCATION, pool_payload, tag)).get_output_in_json()

    def wait_for_replication_status(self, target_state, rg_r, account_name_r, pool_name_r, volume_name_r):
        # python isn't good at do-while loops but loop until we get the target state
        attempts = 0
        if (self.is_live or self.in_recording) and target_state == "Mirrored":
            time.sleep(20)
        replication_status = self.cmd("az netappfiles volume replication status -g %s -a %s -p %s -v %s" %
                                      (rg_r, account_name_r, pool_name_r, volume_name_r)).get_output_in_json()
        while attempts < 10:
            attempts += 1
            replication_status = self.cmd("az netappfiles volume replication status -g %s -a %s -p %s -v %s" %
                                          (rg_r, account_name_r, pool_name_r, volume_name_r)).get_output_in_json()
            if replication_status['mirrorState'] == target_state:
                break
            if self.is_live or self.in_recording:
                time.sleep(60)

        assert replication_status['mirrorState'] == target_state

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1 Tag2=Value2 Test=test_create_delete_volumes"

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
        # due to a rp bug we dont get the full resource atm
        # assert volume['dataProtection'] is None

        assert volume['kerberosEnabled'] is False
        assert volume['securityStyle'] == 'Unix'

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} --account-name %s --pool-name %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

        self.cmd("az netappfiles volume delete --resource-group {rg} --account-name %s --pool-name %s --volume-name %s --force --yes" % (account_name, pool_name, volume_name))
        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a %s -p %s" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 0

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_create_volume_with_subnet_in_different_rg(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1 Tag2=Value2 Test=test_create_delete_volumes"

        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name  # creation_token
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)

        subnet_rg = self.create_random_name(prefix='cli-rg-subnet', length=24)
        subs_id = self.current_subscription()
        self.cmd("az group create -n %s --subscription %s -l %s --tags 'owner=cli_test'" % (subnet_rg, subs_id, VNET_LOCATION)).get_output_in_json()

        rg = '{rg}'
        self.setup_vnet(subnet_rg, vnet_name, subnet_name, '10.0.0.0', VNET_LOCATION)
        self.cmd("az netappfiles account create -g %s -a %s -l %s" % (rg, account_name, RG_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % (rg, account_name, pool_name, RG_LOCATION, POOL_DEFAULT)).get_output_in_json()

        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, subnet_rg, vnet_name, subnet_name)

        volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --subnet %s" % (rg, account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, file_path, subnet_id)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        self.cmd("az netappfiles volume delete --resource-group %s --account-name %s --pool-name %s --volume-name %s --yes" % (rg, account_name, pool_name, volume_name))
        self.cmd("az group delete --yes -n %s" % (subnet_rg))

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume2_', parameter_name='replication_resourcegroup', additional_tags={'owner': 'cli_test'})
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

        self.setup_vnet(rg_r, vnet_name, subnet_name, '10.1.0.0', DP_RG_LOCATION)
        self.cmd("az netappfiles account create -g %s -a %s -l %s" % (rg_r, account_name_r, DP_RG_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % (rg_r, account_name_r, pool_name_r, DP_RG_LOCATION, POOL_DEFAULT)).get_output_in_json()

        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, rg_r, vnet_name, subnet_name)

        dst_volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s --volume-type %s --endpoint-type %s --replication-schedule %s --remote-volume-resource-id %s" % (rg_r, account_name_r, pool_name_r, volume_name_r, DP_RG_LOCATION, VOLUME_DEFAULT, file_path, vnet_name, subnet_id, "DataProtection", "dst", "_10minutely", src_volume['id'])).get_output_in_json()
        assert dst_volume['dataProtection'] is not None
        assert dst_volume['id'] is not None

        if self.is_live or self.in_recording:
            time.sleep(90)

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
        self.cmd("az netappfiles volume replication suspend -g %s -a %s -p %s -v %s -f %s" % (rg_r, account_name_r, pool_name_r, volume_name_r, True))
        self.wait_for_replication_status("Broken", rg_r, account_name_r, pool_name_r, volume_name_r)

        # delete
        self.cmd("az netappfiles volume replication remove -g %s -a %s -p %s -v %s" % (rg_r, account_name_r, pool_name_r, volume_name_r))
        if self.is_live or self.in_recording:
            time.sleep(2)

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_list_volumes(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name1 = self.create_random_name(prefix='cli-vol-', length=24)
        volume_name2 = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag1=Value1"

        self.create_volume(account_name, pool_name, volume_name1, '{rg}', tags=tags, volume_name2=volume_name2)

        volume_list = self.cmd("netappfiles volume list --resource-group {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 2

        self.cmd("az netappfiles volume delete -g {rg} -a %s -p %s -v %s --yes" % (account_name, pool_name, volume_name1))
        volume_list = self.cmd("netappfiles volume list -g {rg} -a '%s' -p '%s'" % (account_name, pool_name)).get_output_in_json()
        assert len(volume_list) == 1

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_get_volume_by_name(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        tags = "Tag2=Value1"

        protocol_types = "NFSv4.1"
        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', tags=tags, protocols=protocol_types, rule_index=1)
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

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
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

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_export_policy(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # now add an export policy
        # there is already one default rule present
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s "
                                          "--allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true "
                                          "--unix-read-write false --cifs false --nfsv3 true --nfsv41 false "
                                          "--has-root-access false" %
                                          (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][0]['allowedClients'] == '0.0.0.0/0'
        assert vol_with_export_policy['exportPolicy']['rules'][1]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][1]['ruleIndex'] == 3
        assert vol_with_export_policy['exportPolicy']['rules'][1]['cifs'] is False
        assert vol_with_export_policy['exportPolicy']['rules'][1]['hasRootAccess'] is False

        # and add another export policy
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.4.0/24' --rule-index 2 --unix-read-only true --unix-read-write false --cifs true --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][1]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][2]['allowedClients'] == '1.2.4.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][2]['ruleIndex'] == 2
        #CIFS is no longer updated check why
        #assert vol_with_export_policy['exportPolicy']['rules'][0]['cifs'] is True
        # assert len(vol_with_export_policy['exportPolicy']['rules']) == 3

        # list the policies
        export_policy = self.cmd("netappfiles volume export-policy list -g {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert len(export_policy['rules']) == 3
        assert export_policy['rules'][1]['allowedClients'] == '1.2.3.0/24'
        assert export_policy['rules'][2]['allowedClients'] == '1.2.4.0/24'
        # and remove one
        self.cmd("netappfiles volume export-policy remove -g {rg} -a %s -p %s -v %s --rule-index 3 --yes" % (account_name, pool_name, volume_name))
        #
        if self.is_live or self.in_recording:
            time.sleep(240)
        volume = self.cmd("az netappfiles volume show --resource-group {rg} -a %s -p %s -v %s" % (account_name, pool_name, volume_name)).get_output_in_json()
        # assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # assert len(volume['exportPolicy']['rules']) == 2

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_non_default_export_policy(self):
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
        assert vol_with_export_policy['exportPolicy']['rules'][1]['allowedClients'] == '1.2.3.0/24'
        assert vol_with_export_policy['exportPolicy']['rules'][1]['ruleIndex'] == 3
        assert vol_with_export_policy['exportPolicy']['rules'][1]['cifs'] is False
        # and recheck the other properties are unchanged
        assert volume['usageThreshold'] == 200 * GIB_SCALE
        assert volume['serviceLevel'] == "Standard"

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_create_volume_with_non_default_export_policy(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        file_path = volume_name  # creation_token
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        protocol_types = "NFSv4.1"
        tag = "Tag2=Value1"
        rule_index = 2
        unix_read_only = False
        unix_read_write = True
        cifs = False
        nfsv3 = False
        nfsv41 = True
        allowed_clients = '1.2.3.0/24'

        self.prepare_for_volume_creation('{rg}', account_name, pool_name, vnet_name, subnet_name)

        # Error when allowed-clients not set on NFSv4.1
        with self.assertRaises(ValidationError):
            self.cmd("az netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s "
                     "--subnet %s --protocol-types %s --tags %s --rule-index %s --unix-read-only %s "
                     "--unix-read-write %s --cifs %s" %
                     (account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, file_path, vnet_name,
                      subnet_name, protocol_types, tag, rule_index, unix_read_only, unix_read_write, cifs))

        volume = self.cmd("az netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s %s --file-path %s --vnet %s "
                          "--subnet %s --protocol-types %s --tags %s --rule-index %s --unix-read-only %s "
                          "--unix-read-write %s --cifs %s --allowed-clients %s" %
                          (account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, file_path,
                           vnet_name, subnet_name, protocol_types, tag, rule_index, unix_read_only, unix_read_write,
                           cifs, allowed_clients)).get_output_in_json()

        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # specified protocol type
        assert len(volume['protocolTypes']) == 1
        assert volume['protocolTypes'][0] == 'NFSv4.1'
        assert len(volume['exportPolicy']['rules']) == 1
        assert volume['exportPolicy']['rules'][0]['ruleIndex'] == rule_index
        assert volume['exportPolicy']['rules'][0]['unixReadOnly'] == unix_read_only
        assert volume['exportPolicy']['rules'][0]['unixReadWrite'] == unix_read_write
        assert volume['exportPolicy']['rules'][0]['nfsv41'] == nfsv41
        assert volume['exportPolicy']['rules'][0]['nfsv3'] == nfsv3
        assert volume['exportPolicy']['rules'][0]['cifs'] == cifs
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == allowed_clients

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_change_pool(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool2_name = self.create_random_name(prefix='cli-pool-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # create a new pool to move the volume to
        pool2 = self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % ('{rg}', account_name, pool2_name, RG_LOCATION, POOL_DEFAULT)).get_output_in_json()
        assert pool2['name'] == account_name + '/' + pool2_name

        # change volume to pool2
        self.cmd("az netappfiles volume pool-change -g {rg} -a %s -p %s -v %s -d %s" % (account_name, pool_name, volume_name, pool2['id']))

        # Make sure that the volume was changed to pool2
        volume = self.cmd("az netappfiles volume show -g {rg} -a %s -p %s -v %s" % (account_name, pool2_name, volume_name)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool2_name + '/' + volume_name

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_volume_parameters(self):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        smb_encryption = False
        smb_continuously_avl = False
        encryption_key_source = "Microsoft.NetApp"
        ldap_enabled = False
        is_default_quota_enabled = False
        avs_data_store = "Disabled"

        self.prepare_for_volume_creation('{rg}', account_name, pool_name, vnet_name, subnet_name)
        volume = self.cmd("az netappfiles volume create --resource-group {rg} --account-name %s --pool-name %s "
                          "--volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s --smb-encryption %s "
                          "--smb-continuously-avl %s --encryption-key-source %s --ldap-enabled %s "
                          "--is-def-quota-enabled %s --avs-data-store %s" %
                          (account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, volume_name, vnet_name,
                           subnet_name, smb_encryption, smb_continuously_avl, encryption_key_source, ldap_enabled,
                           is_default_quota_enabled, avs_data_store)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert volume['smbEncryption'] == smb_encryption
        assert volume['smbContinuouslyAvailable'] == smb_continuously_avl
        assert volume['encryptionKeySource'] == encryption_key_source
        assert volume['ldapEnabled'] == ldap_enabled
        assert volume['isDefaultQuotaEnabled'] == is_default_quota_enabled
        assert volume['avsDataStore'] == avs_data_store

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_nfsv3_with_no_export_policy_provided_is_successful(self):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.prepare_for_volume_creation('{rg}', account_name, pool_name, vnet_name, subnet_name)
        volume = self.cmd("az netappfiles volume create --resource-group {rg} --account-name %s --pool-name %s "
                          "--volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s --protocol-types NFSv3" %
                          (account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, volume_name, vnet_name,
                           subnet_name)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert len(volume['exportPolicy']['rules']) == 1
        assert volume['exportPolicy']['rules'][0]['nfsv3']

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_nfsv3_with_abn_export_policy_provided_is_successful(self):
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        allowed_clients = "1.2.3.0/24"
        self.prepare_for_volume_creation('{rg}', account_name, pool_name, vnet_name, subnet_name)
        volume = self.cmd("az netappfiles volume create --resource-group {rg} --account-name %s --pool-name %s "
                          "--volume-name %s -l %s %s --file-path %s --vnet %s --subnet %s --protocol-types NFSv3 --allowed-clients %s --rule-index 1 --unix-read-write true" %
                          (account_name, pool_name, volume_name, RG_LOCATION, VOLUME_DEFAULT, volume_name, vnet_name,
                           subnet_name,allowed_clients)).get_output_in_json()
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert len(volume['exportPolicy']['rules']) == 1
        assert volume['exportPolicy']['rules'][0]['nfsv3']
        assert volume['exportPolicy']['rules'][0]['allowedClients'] == allowed_clients

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_add_export_policy_with_no_rule_index(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool_payload = "--service-level 'Standard' --size 8"
        volume_payload = "--service-level 'Standard' --usage-threshold 200"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', pool_payload=pool_payload, volume_payload=volume_payload)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # add an export policy
        # there is already one default rule present
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        assert vol_with_export_policy['exportPolicy']['rules'][1]['ruleIndex'] == 3

        # add another export policy with no rule_index,
        # should result in default rule index of 4 since highest existing rule index is 3
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        assert vol_with_export_policy['exportPolicy']['rules'][2]['ruleIndex'] == 4

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_add_export_policy_with_invalid_rule_index(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool_payload = "--service-level 'Standard' --size 8"
        volume_payload = "--service-level 'Standard' --usage-threshold 200"

        self.create_volume(account_name, pool_name, volume_name, '{rg}', pool_payload=pool_payload, volume_payload=volume_payload)

        # add an export policy
        # there is already one default rule present
        vol_with_export_policy = self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()
        # assert vol_with_export_policy['name'] == account_name + '/' + pool_name + '/' + volume_name
        # assert vol_with_export_policy['exportPolicy']['rules'][0]['ruleIndex'] == 3

        # add another export policy with same rule_index, should result in validation error -> no longer applies with generated code, should be idempotent or update existing rule
        # with self.assertRaisesRegex(ValidationError, "Rule index 3 already exist"):
        self.cmd("netappfiles volume export-policy add -g {rg} -a %s -p %s -v %s --allowed-clients '1.2.3.0/24' --rule-index 3 --unix-read-only true --unix-read-write false --cifs false --nfsv3 true --nfsv41 false" % (account_name, pool_name, volume_name)).get_output_in_json()

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_break_file_locks(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # call breakFileLocks
        self.cmd("az netappfiles volume break-file-locks -g {rg} -a %s -p %s -v %s -y" % (account_name, pool_name, volume_name))

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_get_groupid_list_for_ldapuser(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        username = self.create_random_name(prefix='fakeuser-', length=15    )

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name

        # call getGroupId
        with self.assertRaises(HttpResponseError) as cm:
            self.cmd("az netappfiles volume get-groupid-list-for-ldapuser -g {rg} -a %s -p %s -v %s --username %s" % (account_name, pool_name, volume_name, username))
        self.assertIn('GroupIdListForLDAPUserNotSupportedVolumes', str(
            cm.exception))

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_network_sibling_sets(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}')
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        self.kwargs.update({
            'subnet_id': volume['subnetId'],
            'networkSiblingSetId': volume['networkSiblingSetId'],
            'loc': RG_LOCATION
        })
        # call query-network-sibling-set
        networkSiblingSet = self.cmd("az netappfiles query-network-sibling-set -l {loc} --subnet-id {subnet_id} --network-sibling-set-id {networkSiblingSetId}" ).get_output_in_json()
        self.kwargs.update({
            'networkSiblingSetStateId': networkSiblingSet['networkSiblingSetStateId'],
            'networkFeatures':'Standard'
        })

        networkSiblingSet = self.cmd("az netappfiles update-network-sibling-set -l {loc} --subnet-id {subnet_id} --network-sibling-set-id {networkSiblingSetId} --network-sibling-set-state-id='{networkSiblingSetStateId}' --network-features {networkFeatures}").get_output_in_json()
    
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_volume_size_8Tib(self):
        # tests that adding export policy works with non-default service level/usage threshold
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool_payload = "--service-level 'Standard' --size 8"
        volume_payload = "--service-level 'Standard' --usage-threshold 8192"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', pool_payload=pool_payload, volume_payload=volume_payload)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # check the specified volume properties
        assert volume['usageThreshold'] == 8192 * GIB_SCALE
        assert volume['serviceLevel'] == "Standard"

    @serial_test()
    @unittest.skip('Skip for sizing quotas on regions')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_volume_size_50Gib(self):
        # tests that adding export policy works with non-default service level/usage threshold
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        pool_payload = "--service-level 'Standard' --size 8"
        volume_payload = "--service-level 'Standard' --usage-threshold 50"

        volume = self.create_volume(account_name, pool_name, volume_name, '{rg}', pool_payload=pool_payload, volume_payload=volume_payload)
        assert volume['name'] == account_name + '/' + pool_name + '/' + volume_name
        # check the specified volume properties
        # assert volume['usageThreshold'] == 8192 * GIB_SCALE
        assert volume['serviceLevel'] == "Standard"

    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_volume_', additional_tags={'owner': 'cli_test'})
    def test_exernal_migration_volume_fails(self):
        # create source volume
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)        
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)        
        rg = '{rg}'
        external_host_name = "externalHostName"
        external_server_name = "externalServerName"
        external_volume_name = "externalVolumeName"
        # create destination volume in other region/rg and with its own vnet
        vnet_name = self.create_random_name(prefix='cli-vnet-', length=24)
        file_path = volume_name  # creation_token
        subnet_name = self.create_random_name(prefix='cli-subnet-', length=16)
        # rg_r = self.create_random_name(prefix='cli-rg-', length=24)        
        subs_id = self.current_subscription()
        volumeType = "Migration"
        self.setup_vnet(rg, vnet_name, subnet_name, '10.1.0.0', DP_RG_LOCATION)
        self.cmd("az netappfiles account create -g %s -a %s -l %s" % (rg, account_name, DP_RG_LOCATION)).get_output_in_json()
        self.cmd("az netappfiles pool create -g %s -a %s -p %s -l %s %s" % (rg, account_name, pool_name, DP_RG_LOCATION, POOL_DEFAULT)).get_output_in_json()

        subnet_id = "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/virtualNetworks/%s/subnets/%s" % (subs_id, rg, vnet_name, subnet_name)        
        dst_volume = self.cmd("az netappfiles volume create --resource-group %s --account-name %s --pool-name %s --volume-name %s -l %s %s --volume-type %s --file-path %s --vnet %s --subnet %s --external-host-name %s --external-server-name %s --external-volume-name %s" % (rg, account_name, pool_name, volume_name, DP_RG_LOCATION, VOLUME_DEFAULT, volumeType, file_path, vnet_name, subnet_id, external_host_name, external_server_name, external_volume_name)).get_output_in_json()
        assert dst_volume['dataProtection'] is not None
        assert dst_volume['id'] is not None

        if self.is_live or self.in_recording:
            time.sleep(90)

        # Peer external cluster
        peerIpAddresses = ["0.0.0.1","0.0.0.2","0.0.0.3","0.0.0.4","0.0.0.5","0.0.0.6"]
        with self.assertRaises(HttpResponseError) as cm:
            self.cmd("az netappfiles volume replication peer-external-cluster -g %s -a %s -p %s -v %s --peer-ip-addresses %s" % (rg, account_name, pool_name, volume_name, peerIpAddresses))  
        # self.assertIn('GroupIdListForLDAPUserNotSupportedVolumes', str(
        #     cm.exception))

        # Authorize external cluster
        with self.assertRaises(HttpResponseError) as cm:
            self.cmd("az netappfiles volume replication authorize-external-replication -g %s -a %s -p %s -v %s " % (rg, account_name, pool_name, volume_name))        
        self.assertIn('peer targeting', str(
           cm.exception))

        # Perform external cluster transfer
        with self.assertRaises(HttpResponseError) as cm:
            self.cmd("az netappfiles volume replication perform-replication-transfer -g %s -a %s -p %s -v %s " % (rg, account_name, pool_name, volume_name))        
        self.assertIn('VolumeReplicationHasNotBeenCreated', str(
            cm.exception))

        # Finalize external cluster transfer
        with self.assertRaises(HttpResponseError) as cm:
            self.cmd("az netappfiles volume replication finalize-external-replication -g %s -a %s -p %s -v %s " % (rg, account_name, pool_name, volume_name))        
        self.assertIn('VolumeReplicationMissingFor', str(
            cm.exception))


        self.cmd("az netappfiles volume delete -g {rg} -a %s -p %s -v %s --yes" % (account_name, pool_name, volume_name))
        
        