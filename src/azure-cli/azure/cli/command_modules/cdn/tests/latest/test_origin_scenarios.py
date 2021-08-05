# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, JMESPathCheck, record_only
from .scenario_mixin import CdnScenarioMixin


class CdnOriginScenarioTest(CdnScenarioMixin, ScenarioTest):

    @record_only()  # This tests relies on a specific subscription with existing resources
    @ResourceGroupPreparer()
    def test_origin_crud(self, resource_group):

        pls_subscription_id = '27cafca8-b9a4-4264-b399-45d0c9cca1ab'
        # Workaround for overly heavy-handed subscription id replacement in playback mode.
        if self.is_playback_mode():
            pls_subscription_id = '00000000-0000-0000-0000-000000000000'
        private_link_id = f'/subscriptions/{pls_subscription_id}/resourceGroups/cdn-sdk-test/providers/Microsoft.Network/privateLinkServices/cdn-sdk-pls-test'
        private_link_location = 'EastUS'
        private_link_message = 'Please approve the request'

        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft')

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_host = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin_host)

        checks = [JMESPathCheck('length(origins)', 1)]
        endpoint = self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin1_id = f'{endpoint.json_value["id"]}/origins/{endpoint.json_value["origins"][0]["name"]}'
        origin1_name = endpoint.json_value['origins'][0]['name']
        checks = [JMESPathCheck('name', origin1_name),
                  JMESPathCheck('hostName', origin_host)]
        self.origin_show_cmd(resource_group,
                             endpoint_name,
                             profile_name,
                             endpoint.json_value['origins'][0]['name'],
                             checks=checks)

        checks = [JMESPathCheck('length(@)', 1),
                  JMESPathCheck('@[0].name', origin1_name),
                  JMESPathCheck('@[0].hostName', origin_host)]
        self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        # Create an origin group.
        origin_group_name = 'test-origin-group'
        checks = [JMESPathCheck('name', origin_group_name),
                  JMESPathCheck('length(origins)', 1)]
        origin_group = self.origin_group_create_cmd(resource_group, origin_group_name, endpoint_name, profile_name,
                                                    origins=origin1_id, checks=checks)
        checks = [JMESPathCheck('length(@)', 1),
                  JMESPathCheck('@[0].name', origin_group_name)]
        self.origin_group_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)
        checks = [JMESPathCheck('name', origin_group_name)]
        self.origin_group_show_cmd(resource_group, origin_group_name, endpoint_name, profile_name, checks=checks)

        # Set the default origin group by name and ID.
        default_origin_group_id = origin_group.json_value['id']
        checks = [JMESPathCheck('defaultOriginGroup.id', default_origin_group_id, case_sensitive=False)]
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=f"--default-origin-group={origin_group_name}",
                                 checks=checks)
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=f"--default-origin-group={default_origin_group_id}",
                                 checks=checks)

        # Create second and third origins.
        origin2_name = self.create_random_name(prefix='origin', length=24)
        origin2_hostname = 'abc.contoso.com'
        http_port = 8080
        https_port = 8443
        origin_host_header = 'abc.contoso.com'
        disabled = False
        weight = 534
        priority = 3
        private_link_id = private_link_id
        private_link_location = private_link_location
        private_link_message = private_link_message
        checks = [JMESPathCheck('name', origin2_name),
                  JMESPathCheck('hostName', origin2_hostname),
                  JMESPathCheck('httpPort', http_port),
                  JMESPathCheck('httpsPort', https_port),
                  JMESPathCheck('originHostHeader', origin_host_header),
                  JMESPathCheck('enabled', not disabled),
                  JMESPathCheck('weight', weight),
                  JMESPathCheck('priority', priority)]
        self.origin_create_cmd(resource_group, origin2_name, endpoint_name, profile_name,
                               host_name=origin2_hostname,
                               http_port=http_port,
                               https_port=https_port,
                               origin_host_header=origin_host_header,
                               disabled=disabled,
                               weight=weight,
                               priority=priority,
                               private_link_id=private_link_id,
                               private_link_location=private_link_location,
                               private_link_message=private_link_message,
                               checks=checks)
        checks = [JMESPathCheck('length(@)', 2)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        disabled = True
        origin3_name = self.create_random_name(prefix='origin', length=24)
        checks = [JMESPathCheck('name', origin3_name),
                  JMESPathCheck('hostName', origin2_hostname),
                  JMESPathCheck('httpPort', http_port),
                  JMESPathCheck('httpsPort', https_port),
                  JMESPathCheck('originHostHeader', origin_host_header),
                  JMESPathCheck('enabled', not disabled),
                  JMESPathCheck('weight', weight),
                  JMESPathCheck('priority', priority)]
        self.origin_create_cmd(resource_group, origin3_name, endpoint_name, profile_name,
                               host_name=origin2_hostname,
                               http_port=http_port,
                               https_port=https_port,
                               origin_host_header=origin_host_header,
                               disabled=disabled,
                               weight=weight,
                               priority=priority,
                               private_link_id=private_link_id,
                               private_link_location=private_link_location,
                               private_link_message=private_link_message,
                               checks=checks)
        checks = [JMESPathCheck('length(@)', 3)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        # Create a second origin group.
        origin2_id = origins.json_value[1]["id"]
        origin3_id = origins.json_value[2]["id"]
        origin_group_2_name = 'test-origin-group-2'
        probe_method = 'GET'
        probe_path = "/healthz"
        probe_protocol = "Https"
        probe_interval = 120
        # Uncomment these once support for response error detection is added in RP
        # response_error_detection_error_types = 'TcpErrorsOnly'
        # response_error_detection_failover_threshold = 5
        # response_error_detection_status_code_ranges = '300-310,400-599'
        checks = [JMESPathCheck('name', origin_group_2_name),
                  JMESPathCheck('origins[0].id', origin2_id, case_sensitive=False),
                  JMESPathCheck('origins[1].id', origin3_id, case_sensitive=False),
                  JMESPathCheck('healthProbeSettings.probeRequestType', probe_method),
                  JMESPathCheck('healthProbeSettings.probePath', probe_path),
                  JMESPathCheck('healthProbeSettings.probeProtocol', probe_protocol),
                  JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', probe_interval),
                  JMESPathCheck('responseBasedOriginErrorDetectionSettings', None)]
        self.origin_group_create_cmd(resource_group, origin_group_2_name, endpoint_name, profile_name,
                                     origins=f'{origin2_name},{origin3_name}',
                                     probe_method=probe_method,
                                     probe_path=probe_path,
                                     probe_protocol=probe_protocol,
                                     probe_interval=probe_interval,
                                     # Uncomment these once support for response error detection is added in RP
                                     #  response_error_detection_error_types=response_error_detection_error_types,
                                     #  response_error_detection_failover_threshold=response_error_detection_failover_threshold,
                                     #  response_error_detection_status_code_ranges=response_error_detection_status_code_ranges,
                                     checks=checks)
        checks = [JMESPathCheck('name', origin_group_name)]
        self.origin_group_show_cmd(resource_group, origin_group_name, endpoint_name, profile_name, checks=checks)
        checks = [JMESPathCheck('length(@)', 2)]
        self.origin_group_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        # Delete the second origin group.
        self.origin_group_delete_cmd(resource_group, origin_group_2_name, endpoint_name, profile_name)
        checks = [JMESPathCheck('length(@)', 1)]
        self.origin_group_list_cmd(resource_group, endpoint_name, profile_name)

        # Update the first origin group.
        origins_list = f'{origin1_id},{origin2_name}'
        probe_method = 'GET'
        probe_path = "/healthz"
        probe_protocol = "Https"
        probe_interval = 60
        # Uncomment these once support for response error detection is added in RP
        # error_types = 'TcpAndHttpErrors'
        # failover_threshold = 15
        # status_code_ranges = '300-310,400-599'
        checks = [JMESPathCheck('name', origin_group_name),
                  JMESPathCheck('origins[0].id', origin1_id, case_sensitive=False),
                  JMESPathCheck('origins[1].id', origin2_id, case_sensitive=False),
                  JMESPathCheck('healthProbeSettings.probeRequestType', probe_method),
                  JMESPathCheck('healthProbeSettings.probePath', probe_path),
                  JMESPathCheck('healthProbeSettings.probeProtocol', probe_protocol),
                  JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', probe_interval),
                  JMESPathCheck('responseBasedOriginErrorDetectionSettings', None)]
        self.origin_group_update_cmd(resource_group,
                                     origin_group_name,
                                     endpoint_name,
                                     profile_name,
                                     origins=origins_list,
                                     probe_method=probe_method,
                                     probe_path=probe_path,
                                     probe_protocol=probe_protocol,
                                     probe_interval=probe_interval,
                                     # Uncomment these once support for response error detection is added in RP
                                     #  error_types=error_types,
                                     #  failover_threshold=failover_threshold,
                                     #  status_code_ranges=status_code_ranges,
                                     checks=checks)
        # Validate that unset fields aren't modified
        self.origin_group_update_cmd(resource_group,
                                     origin_group_name,
                                     endpoint_name,
                                     profile_name,
                                     origins=origins_list,
                                     checks=checks)

        # Update the first origin.
        origin_name = origins.json_value[0]["name"]
        checks = [JMESPathCheck('name', origin_name),
                  JMESPathCheck('httpPort', 8080),
                  JMESPathCheck('httpsPort', 8443),
                  JMESPathCheck('privateLinkResourceId', private_link_id),
                  JMESPathCheck('privateLinkLocation', private_link_location),
                  JMESPathCheck('privateLinkApprovalMessage', private_link_message)]
        self.origin_update_cmd(resource_group,
                               origin_name,
                               endpoint_name,
                               profile_name,
                               http_port='8080',
                               https_port='8443',
                               origin_host_header=origin_host_header,
                               disabled=True,
                               priority=priority,
                               weight=weight,
                               private_link_id=private_link_id,
                               private_link_location=private_link_location,
                               private_link_message=private_link_message,
                               checks=checks)

        checks = [JMESPathCheck('name', origin_name),
                  JMESPathCheck('httpPort', 8080),
                  JMESPathCheck('httpsPort', 8443),
                  JMESPathCheck('privateLinkResourceId', private_link_id),
                  JMESPathCheck('privateLinkLocation', private_link_location),
                  JMESPathCheck('privateLinkApprovalMessage', private_link_message)]
        self.origin_show_cmd(resource_group,
                             endpoint_name,
                             profile_name,
                             origin_name,
                             checks=checks)

        # Delete the second origin.
        self.origin_delete_cmd(resource_group, origin3_name, endpoint_name, profile_name)
        checks = [JMESPathCheck('length(@)', 2)]
        self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

    @ResourceGroupPreparer()
    def test_microsoft_sku_origingroup_override(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=16)
        self.profile_create_cmd(resource_group, profile_name, sku='Standard_Microsoft')

        endpoint_name = self.create_random_name(prefix='endpoint', length=24)
        origin_host = f'{endpoint_name}.contoso.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin_host)

        checks = [JMESPathCheck('length(origins)', 1)]
        endpoint = self.endpoint_show_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin1_id = f'{endpoint.json_value["id"]}/origins/{endpoint.json_value["origins"][0]["name"]}'
        origin1_name = endpoint.json_value['origins'][0]['name']
        checks = [JMESPathCheck('name', origin1_name),
                  JMESPathCheck('hostName', origin_host)]
        self.origin_show_cmd(resource_group,
                             endpoint_name,
                             profile_name,
                             endpoint.json_value['origins'][0]['name'],
                             checks=checks)

        # Create an origin group.
        origin_group_name = 'test-origin-group'
        checks = [JMESPathCheck('name', origin_group_name),
                  JMESPathCheck('length(origins)', 1)]
        origin_group = self.origin_group_create_cmd(resource_group, origin_group_name, endpoint_name, profile_name,
                                                    origins=origin1_id, checks=checks)
        checks = [JMESPathCheck('length(@)', 1),
                  JMESPathCheck('@[0].name', origin_group_name)]
        self.origin_group_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)
        checks = [JMESPathCheck('name', origin_group_name)]
        self.origin_group_show_cmd(resource_group, origin_group_name, endpoint_name, profile_name, checks=checks)

        # Set the default origin group.
        default_origin_group_id = origin_group.json_value['id']
        checks = [JMESPathCheck('defaultOriginGroup.id', default_origin_group_id, case_sensitive=False)]
        self.endpoint_update_cmd(resource_group,
                                 endpoint_name,
                                 profile_name,
                                 options=f"--default-origin-group={origin_group_name}",
                                 checks=checks)

        # Create two origin gorups.
        origin2_name = self.create_random_name(prefix='origin', length=24)
        origin2_hostname = f'{origin2_name}.contoso.com'
        http_port = 8080
        https_port = 8443
        weight = 534
        priority = 3
        checks = [JMESPathCheck('name', origin2_name),
                  JMESPathCheck('hostName', origin2_hostname),
                  JMESPathCheck('httpPort', http_port),
                  JMESPathCheck('httpsPort', https_port),
                  JMESPathCheck('originHostHeader', origin2_hostname),
                  JMESPathCheck('enabled', True),
                  JMESPathCheck('weight', weight),
                  JMESPathCheck('priority', priority)]
        self.origin_create_cmd(resource_group, origin2_name, endpoint_name, profile_name,
                               host_name=origin2_hostname,
                               http_port=http_port,
                               https_port=https_port,
                               origin_host_header=origin2_hostname,
                               disabled=False,
                               weight=weight,
                               priority=priority,
                               checks=checks)
        checks = [JMESPathCheck('length(@)', 2)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin3_name = self.create_random_name(prefix='origin', length=24)
        origin3_hostname = f'{origin3_name}.contoso.com'
        checks = [JMESPathCheck('name', origin3_name),
                  JMESPathCheck('hostName', origin3_hostname),
                  JMESPathCheck('httpPort', http_port),
                  JMESPathCheck('httpsPort', https_port),
                  JMESPathCheck('originHostHeader', origin3_hostname),
                  JMESPathCheck('enabled', True),
                  JMESPathCheck('weight', weight),
                  JMESPathCheck('priority', priority)]
        self.origin_create_cmd(resource_group, origin3_name, endpoint_name, profile_name,
                               host_name=origin3_hostname,
                               http_port=http_port,
                               https_port=https_port,
                               origin_host_header=origin3_hostname,
                               disabled=False,
                               weight=weight,
                               priority=priority,
                               checks=checks)
        checks = [JMESPathCheck('length(@)', 3)]
        origins = self.origin_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        origin2_id = origins.json_value[1]["id"]
        origin3_id = origins.json_value[2]["id"]
        origin_group_2_name = 'test-origin-group-2'
        origin_group_3_name = 'test-origin-group-3'
        probe_method = 'GET'
        probe_path = "/healthz"
        probe_protocol = "Https"
        probe_interval = 120
        checks = [JMESPathCheck('name', origin_group_2_name),
                  JMESPathCheck('origins[0].id', origin2_id, case_sensitive=False),
                  JMESPathCheck('healthProbeSettings.probeRequestType', probe_method),
                  JMESPathCheck('healthProbeSettings.probePath', probe_path),
                  JMESPathCheck('healthProbeSettings.probeProtocol', probe_protocol),
                  JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', probe_interval),
                  JMESPathCheck('responseBasedOriginErrorDetectionSettings', None)]
        self.origin_group_create_cmd(resource_group, origin_group_2_name, endpoint_name, profile_name,
                                     origins=f'{origin2_name}',
                                     probe_method=probe_method,
                                     probe_path=probe_path,
                                     probe_protocol=probe_protocol,
                                     probe_interval=probe_interval,
                                     checks=checks)

        checks = [JMESPathCheck('name', origin_group_3_name),
                  JMESPathCheck('origins[0].id', origin3_id, case_sensitive=False),
                  JMESPathCheck('healthProbeSettings.probeRequestType', probe_method),
                  JMESPathCheck('healthProbeSettings.probePath', probe_path),
                  JMESPathCheck('healthProbeSettings.probeProtocol', probe_protocol),
                  JMESPathCheck('healthProbeSettings.probeIntervalInSeconds', probe_interval),
                  JMESPathCheck('responseBasedOriginErrorDetectionSettings', None)]
        self.origin_group_create_cmd(resource_group, origin_group_3_name, endpoint_name, profile_name,
                                     origins=f'{origin3_name}',
                                     probe_method=probe_method,
                                     probe_path=probe_path,
                                     probe_protocol=probe_protocol,
                                     probe_interval=probe_interval,
                                     checks=checks)

        checks = [JMESPathCheck('length(@)', 3)]
        orgin_groups = self.origin_group_list_cmd(resource_group, endpoint_name, profile_name, checks=checks)

        # Specify origin group override by id
        origin_group_2_id = orgin_groups.json_value[1]["id"]
        rule_name = 'r1'
        msg = 'az cdn endpoint rule add -g {} -n {} --profile-name {} --order {} --rule-name {}\
               --match-variable UrlPath --operator BeginsWith --match-values "/test1"\
               --action-name OriginGroupOverride --origin-group {}'
        command = msg.format(resource_group,
                             endpoint_name,
                             profile_name,
                             1,
                             rule_name,
                             origin_group_2_id)
        add_rule_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules)', 1),
                         JMESPathCheck('deliveryPolicy.rules[0].name', rule_name),
                         JMESPathCheck('deliveryPolicy.rules[0].order', 1),
                         JMESPathCheck('deliveryPolicy.rules[0].actions[0].name', "OriginGroupOverride"),
                         JMESPathCheck('deliveryPolicy.rules[0].actions[0].parameters.originGroup.id', origin_group_2_id),
                         JMESPathCheck('deliveryPolicy.rules[0].conditions[0].name', "UrlPath"),
                         JMESPathCheck('deliveryPolicy.rules[0].conditions[0].parameters.matchValues[0]', "/test1"),
                         JMESPathCheck('deliveryPolicy.rules[0].conditions[0].parameters.operator', "BeginsWith")]
        self.cmd(command, checks=add_rule_checks)

        # Specify origin group override by name
        rule_name = 'r2'
        origin_group_3_id = orgin_groups.json_value[2]["id"]
        msg = 'az cdn endpoint rule add -g {} -n {} --profile-name {} --order {} --rule-name {}\
               --match-variable UrlPath --operator BeginsWith --match-values "/test2"\
               --action-name OriginGroupOverride --origin-group {}'
        command = msg.format(resource_group,
                             endpoint_name,
                             profile_name,
                             2,
                             rule_name,
                             origin_group_3_name)
        add_rule_checks = [JMESPathCheck('name', endpoint_name),
                         JMESPathCheck('length(deliveryPolicy.rules)', 2),
                         JMESPathCheck('deliveryPolicy.rules[1].name', rule_name),
                         JMESPathCheck('deliveryPolicy.rules[1].order', 2),
                         JMESPathCheck('deliveryPolicy.rules[1].actions[0].name', "OriginGroupOverride"),
                         JMESPathCheck('deliveryPolicy.rules[1].actions[0].parameters.originGroup.id', origin_group_3_id),
                         JMESPathCheck('deliveryPolicy.rules[1].conditions[0].name', "UrlPath"),
                         JMESPathCheck('deliveryPolicy.rules[1].conditions[0].parameters.matchValues[0]', "/test2"),
                         JMESPathCheck('deliveryPolicy.rules[1].conditions[0].parameters.operator', "BeginsWith")]
        self.cmd(command, checks=add_rule_checks)
