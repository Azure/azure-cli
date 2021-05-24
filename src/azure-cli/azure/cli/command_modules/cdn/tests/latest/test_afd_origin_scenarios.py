# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdOriginScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_origin_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name, sku="Premium_AzureFrontDoor")

        origin_group_name = self.create_random_name(prefix='og', length=16)
        self.afd_origin_group_create_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         "--probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt "
                                         "--sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50")

        origin_name = self.create_random_name(prefix='origin', length=16)
        create_options = "--host-name plstestcli.blob.core.windows.net " \
                         + "--origin-host-header plstestcli.blob.core.windows.net " \
                         + "--priority 1 --weight 1000 --http-port 80 --https-port 443 --enabled-state Enabled"

        create_checks = [JMESPathCheck('name', origin_name),
                         JMESPathCheck('hostName', "plstestcli.blob.core.windows.net"),
                         JMESPathCheck('httpPort', 80),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 1000),
                         JMESPathCheck('enabledState', "Enabled"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_origin_create_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   create_options,
                                   create_checks)

        origin_name1 = self.create_random_name(prefix='origin', length=16)
        create_options = "--host-name huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--origin-host-header huaiyiztesthost1.blob.core.chinacloudapi.cn " \
                         + "--priority 1 --weight 666 --http-port 8080 --https-port 443 --enabled-state Enabled"

        create_checks = [JMESPathCheck('name', origin_name1),
                         JMESPathCheck('hostName', "huaiyiztesthost1.blob.core.chinacloudapi.cn"),
                         JMESPathCheck('httpPort', 8080),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 666),
                         JMESPathCheck('enabledState', "Enabled"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_origin_create_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name1,
                                   create_options,
                                   create_checks)

        list_checks = [JMESPathCheck('length(@)', 2),
                       JMESPathCheck('@[0].name', origin_name),
                       JMESPathCheck('@[1].name', origin_name1)]
        self.afd_origin_list_cmd(resource_group, profile_name, origin_group_name, checks=list_checks)

        update_checks = [JMESPathCheck('name', origin_name),
                         JMESPathCheck('hostName', "plstestcli.blob.core.windows.net"),
                         JMESPathCheck('httpPort', 8080),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 58),
                         JMESPathCheck('enabledState', "Enabled"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--weight 58 --http-port 8080'
        self.afd_origin_update_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   options=options,
                                   checks=update_checks)

        update_checks = [JMESPathCheck('name', origin_name),
                         JMESPathCheck('hostName', "plstestcli.blob.core.windows.net"),
                         JMESPathCheck('httpPort', 80),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 58),
                         JMESPathCheck('enabledState', "Enabled"),
                         JMESPathCheck('sharedPrivateLinkResource.privateLink.id', f"/subscriptions/{self.get_subscription_id()}/resourceGroups/CliDevReservedGroup/providers/Microsoft.Storage/storageAccounts/plstestcli"),
                         JMESPathCheck('sharedPrivateLinkResource.groupId', "blob"),
                         JMESPathCheck('sharedPrivateLinkResource.privateLinkLocation', "eastus"),
                         JMESPathCheck('sharedPrivateLinkResource.requestMessage', "Private link service from AFD"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--http-port 80 --enable-private-link --private-link-resource ' \
                  + f' /subscriptions/{self.get_subscription_id()}/resourceGroups/CliDevReservedGroup/providers/Microsoft.Storage/storageAccounts/plstestcli' \
                  + ' --private-link-sub-resource blob' \
                  + ' --private-link-location eastus' \
                  + ' --private-link-request-message "Private link service from AFD"'
        self.afd_origin_update_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   options=options,
                                   checks=update_checks)

        update_checks = [JMESPathCheck('name', origin_name),
                         JMESPathCheck('hostName', "plstestcli.blob.core.windows.net"),
                         JMESPathCheck('httpPort', 80),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 58),
                         JMESPathCheck('enabledState', "Enabled"),
                         JMESPathCheck('sharedPrivateLinkResource.privateLink.id', f"/subscriptions/{self.get_subscription_id()}/resourceGroups/CliDevReservedGroup/providers/Microsoft.Storage/storageAccounts/plstestcli"),
                         JMESPathCheck('sharedPrivateLinkResource.groupId', "table"),
                         JMESPathCheck('sharedPrivateLinkResource.privateLinkLocation', "eastus"),
                         JMESPathCheck('sharedPrivateLinkResource.requestMessage', "Private link service from AFD"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--private-link-sub-resource table'
        self.afd_origin_update_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   options=options,
                                   checks=update_checks)

        update_checks = [JMESPathCheck('name', origin_name),
                         JMESPathCheck('hostName', "plstestcli.blob.core.windows.net"),
                         JMESPathCheck('httpPort', 80),
                         JMESPathCheck('httpsPort', 443),
                         JMESPathCheck('priority', 1),
                         JMESPathCheck('weight', 99),
                         JMESPathCheck('enabledState', "Disabled"),
                         JMESPathCheck('sharedPrivateLinkResource', None),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--weight 99 --enable-private-link false --enabled-state Disabled'
        self.afd_origin_update_cmd(resource_group,
                                   profile_name,
                                   origin_group_name,
                                   origin_name,
                                   options=options,
                                   checks=update_checks)

        self.afd_origin_delete_cmd(resource_group, profile_name, origin_group_name, origin_name)
        self.afd_origin_delete_cmd(resource_group, profile_name, origin_group_name, origin_name1)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_origin_list_cmd(resource_group, profile_name, origin_group_name, list_checks)
