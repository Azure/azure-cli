# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin
import datetime


class CdnAfdLogAnalyticScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_log_analytic(self, resource_group):
        profile_name = 'profile123'
        self.afd_profile_create_cmd(resource_group, profile_name)

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        checks = [JMESPathCheck('originResponseTimeoutSeconds', 100),
                  JMESPathCheck('enabledState', 'Enabled')]
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     origin_response_timeout_seconds,
                                     enabled_state,
                                     checks=checks)

        domain = f'{endpoint_name}.z01.azurefd.net'

        start_time = datetime.datetime.now().astimezone().replace(microsecond=0)
        if self.is_playback_mode():
            start_time = datetime.datetime(2021, 4, 2, 10, 23, 7, tzinfo=datetime.timezone.utc)

        end_time = start_time + datetime.timedelta(seconds=300)

        location_list_commands = f"afd log-analytic location list -g {resource_group} --profile-name {profile_name}"
        self.cmd(location_list_commands, expect_failure=False)

        resource_list_commands = f"afd log-analytic resource list -g {resource_group} --profile-name {profile_name}"
        self.cmd(resource_list_commands, expect_failure=False)

        metric_list_commands = f"afd log-analytic metric list -g {resource_group} --profile-name {profile_name} --metrics clientRequestCount " + \
                               f"--date-time-begin {start_time.isoformat()} --granularity PT5M --date-time-end {end_time.isoformat()} --custom-domains {domain} --protocols http --group-by cacheStatus"
        self.cmd(metric_list_commands, expect_failure=False)

        ranking_list_commands = f"afd log-analytic ranking list -g {resource_group} --profile-name {profile_name} --metrics clientRequestCount " + \
                                f"--date-time-begin {start_time.isoformat()} --date-time-end {end_time.isoformat()} --custom-domains {domain} --rankings referrer --max-ranking 10"
        self.cmd(ranking_list_commands, expect_failure=False)

        self.afd_endpoint_delete_cmd(resource_group, endpoint_name, profile_name)

    @ResourceGroupPreparer()
    def test_afd_waf_log_analytic(self, resource_group):
        profile_name = 'profile123'
        self.afd_profile_create_cmd(resource_group, profile_name, sku="Premium_AzureFrontDoor")

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_response_timeout_seconds = 100
        enabled_state = "Enabled"
        checks = [JMESPathCheck('originResponseTimeoutSeconds', 100),
                  JMESPathCheck('enabledState', 'Enabled')]
        self.afd_endpoint_create_cmd(resource_group,
                                     profile_name,
                                     endpoint_name,
                                     origin_response_timeout_seconds,
                                     enabled_state,
                                     checks=checks)

        start_time = datetime.datetime.now().astimezone().replace(microsecond=0)
        if self.is_playback_mode():
            start_time = datetime.datetime(2021, 4, 2, 10, 23, 6, tzinfo=datetime.timezone.utc)

        end_time = start_time + datetime.timedelta(seconds=300)

        metric_list_commands = f"afd waf-log-analytic metric list -g {resource_group} --profile-name {profile_name} --metrics clientRequestCount " + \
                               f"--date-time-begin {start_time.isoformat()} --date-time-end {end_time.isoformat()} --granularity PT5M --rule-types managed"
        self.cmd(metric_list_commands, expect_failure=False)

        ranking_list_commands = f"afd waf-log-analytic ranking list -g {resource_group} --profile-name {profile_name} --metrics clientRequestCount " + \
                                f"--date-time-begin {start_time.isoformat()} --date-time-end {end_time.isoformat()} --rankings action --max-ranking 10"
        self.cmd(ranking_list_commands, expect_failure=False)

        self.afd_endpoint_delete_cmd(resource_group, endpoint_name, profile_name)
