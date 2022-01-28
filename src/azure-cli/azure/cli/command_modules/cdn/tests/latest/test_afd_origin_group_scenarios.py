# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdOriginGroupScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_origin_group_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.afd_profile_create_cmd(resource_group, profile_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_origin_group_list_cmd(resource_group, profile_name, list_checks)

        origin_group_name = self.create_random_name(prefix='og', length=16)
        checks = [JMESPathCheck('name', origin_group_name),
                  JMESPathCheck('loadBalancingSettings.sampleSize', 4),
                  JMESPathCheck('loadBalancingSettings.successfulSamplesRequired', 3),
                  JMESPathCheck('loadBalancingSettings.additionalLatencyInMilliseconds', 50),
                  JMESPathCheck('healthProbeSettings.probePath', "/test1/azure.txt"),
                  JMESPathCheck('healthProbeSettings.probeProtocol', "Http"),
                  JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', 120),
                  JMESPathCheck('healthProbeSettings.probeRequestType', "GET"),
                  JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_origin_group_create_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         "--probe-request-type GET --probe-protocol Http --probe-interval-in-seconds 120 --probe-path /test1/azure.txt " +
                                         "--sample-size 4 --successful-samples-required 3 --additional-latency-in-milliseconds 50",
                                         checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', origin_group_name)]
        self.afd_origin_group_list_cmd(resource_group, profile_name, checks=list_checks)

        update_checks = [JMESPathCheck('name', origin_group_name),
                         JMESPathCheck('loadBalancingSettings.sampleSize', 4),
                         JMESPathCheck('loadBalancingSettings.successfulSamplesRequired', 3),
                         JMESPathCheck('loadBalancingSettings.additionalLatencyInMilliseconds', 50),
                         JMESPathCheck('healthProbeSettings.probePath', "/test1/azure.txt"),
                         JMESPathCheck('healthProbeSettings.probeProtocol', "Https"),
                         JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', 120),
                         JMESPathCheck('healthProbeSettings.probeRequestType', "GET"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--probe-request-type GET --probe-protocol Https'
        self.afd_origin_group_update_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         options=options,
                                         checks=update_checks)

        update_checks = [JMESPathCheck('name', origin_group_name),
                         JMESPathCheck('loadBalancingSettings.sampleSize', 5),
                         JMESPathCheck('loadBalancingSettings.successfulSamplesRequired', 3),
                         JMESPathCheck('loadBalancingSettings.additionalLatencyInMilliseconds', 30),
                         JMESPathCheck('healthProbeSettings.probePath', "/test1/azure.txt"),
                         JMESPathCheck('healthProbeSettings.probeProtocol', "Https"),
                         JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', 120),
                         JMESPathCheck('healthProbeSettings.probeRequestType', "GET"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--sample-size 5 --additional-latency-in-milliseconds 30'
        self.afd_origin_group_update_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         options=options,
                                         checks=update_checks)

        update_checks = [JMESPathCheck('name', origin_group_name),
                         JMESPathCheck('loadBalancingSettings.sampleSize', 4),
                         JMESPathCheck('loadBalancingSettings.successfulSamplesRequired', 3),
                         JMESPathCheck('loadBalancingSettings.additionalLatencyInMilliseconds', 30),
                         JMESPathCheck('healthProbeSettings.probePath', "/test1/azure.txt"),
                         JMESPathCheck('healthProbeSettings.probeProtocol', "Https"),
                         JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', 120),
                         JMESPathCheck('healthProbeSettings.probeRequestType', "HEAD"),
                         JMESPathCheck('provisioningState', 'Succeeded')]
        options = '--sample-size 4 --additional-latency-in-milliseconds 30 --probe-request-type HEAD'
        self.afd_origin_group_update_cmd(resource_group,
                                         profile_name,
                                         origin_group_name,
                                         options=options,
                                         checks=update_checks)

        self.afd_origin_group_delete_cmd(resource_group, profile_name, origin_group_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_origin_group_list_cmd(resource_group, profile_name, list_checks)
