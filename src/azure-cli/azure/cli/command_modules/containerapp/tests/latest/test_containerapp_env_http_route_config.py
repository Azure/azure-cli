# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.command_modules.containerapp._utils import format_location
from azure.mgmt.core.tools import parse_resource_id

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)
from knack.testsdk import live_only

from .utils import create_vnet_subnet

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

from .common import TEST_LOCATION, write_test_file, clean_up_test_file


class ContainerAppEnvHttpRouteConfigTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location="eastus")
    def test_containerapp_env_http_route_config_crudoperations_e2e(self, resource_group):

        app1 = self.create_random_name(prefix='routed1', length=24)
        app2 = self.create_random_name(prefix='routed2', length=24)

        containerapp_yaml_text = f"""
                                location: {TEST_LOCATION}
                                type: Microsoft.App/containerApps
                                properties:
                                  configuration:
                                    activeRevisionsMode: Single
                                    ingress:
                                      external: false
                                      allowInsecure: false
                                      targetPort: 80
                                  template:
                                    revisionSuffix: myrevision
                                    containers:
                                      - image: nginx
                                        name: nginx
                                        env:
                                          - name: HTTP_PORT
                                            value: 80
                                        command:
                                          - npm
                                          - start
                                        resources:
                                          cpu: 0.5
                                          memory: 1Gi
                                    scale:
                                      minReplicas: 1
                                      maxReplicas: 1
                                """
        containerapp_file_name = os.path.join(TEST_DIR, f"{self._testMethodName}_containerapp.yml")
        write_test_file(containerapp_file_name, containerapp_yaml_text)

        http_route_config1_yaml_text = f"""
                                rules:
                                  - description: "rule 1"
                                    routes:
                                      - match:
                                          prefix: "/1"
                                        action:
                                          PrefixRewrite: "/"
                                    targets:
                                      - ContainerApp: "{app1}"
                                """
        http_route_config1_file_name = os.path.join(TEST_DIR, f"{self._testMethodName}_http_route_config1.yml")
        write_test_file(http_route_config1_file_name, http_route_config1_yaml_text)

        http_route_config2_yaml_text = f"""
                                rules:
                                  - description: "rule 2"
                                    routes:
                                      - match:
                                          prefix: "/2"
                                        action:
                                          PrefixRewrite: "/"
                                    targets:
                                      - ContainerApp: "{app2}"
                                """
        http_route_config2_file_name = os.path.join(TEST_DIR, f"{self._testMethodName}_http_route_config2.yml")
        write_test_file(http_route_config2_file_name, http_route_config2_yaml_text)

        self.cmd(f'configure --defaults location={TEST_LOCATION}')

        env_name = self.create_random_name(prefix='aca-http-route-config-env', length=30)
        subnet_id = create_vnet_subnet(self, resource_group, self.create_random_name(prefix='name', length=24), location=format_location(TEST_LOCATION))

        self.cmd(f'containerapp env create -g {resource_group} -n {env_name} --location {TEST_LOCATION}  --logs-destination none --enable-workload-profiles -s {subnet_id}')

        self.cmd(f"az containerapp env http-route-config list -g {resource_group} -n {env_name}", checks=[
            JMESPathCheck('length(@)', 0),
        ])

        self.cmd(f'containerapp create -n {app1} -g {resource_group} --environment {env_name} --yaml "{containerapp_file_name}"')
        self.cmd(f'containerapp show -g {resource_group} -n {app1}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
        ])

        self.cmd(f'containerapp create -n {app2} -g {resource_group} --environment {env_name} --yaml "{containerapp_file_name}"')
        self.cmd(f'containerapp show -g {resource_group} -n {app2}', checks=[
            JMESPathCheck("properties.provisioningState", "Succeeded"),
        ])

        route_name = "route1"

        self.cmd(f"az containerapp env http-route-config create -g {resource_group} -n {env_name} -r {route_name} --yaml '{http_route_config1_file_name}'", checks=[
            JMESPathCheck('properties.rules[0].description', "rule 1"),
            JMESPathCheck('properties.rules[0].routes[0].match.prefix', "/1"),
            JMESPathCheck('properties.rules[0].routes[0].action.prefixRewrite', "/"),
            JMESPathCheck('properties.rules[0].targets[0].containerApp', app1),
        ])

        self.cmd(f"az containerapp env http-route-config show -g {resource_group} -n {env_name} -r {route_name}", checks=[
            JMESPathCheck('properties.rules[0].description', "rule 1"),
            JMESPathCheck('properties.rules[0].routes[0].match.prefix', "/1"),
            JMESPathCheck('properties.rules[0].routes[0].action.prefixRewrite', "/"),
            JMESPathCheck('properties.rules[0].targets[0].containerApp', app1),
        ])

        self.cmd(f"az containerapp env http-route-config list -g {resource_group} -n {env_name}", checks=[
            JMESPathCheck('[0].properties.rules[0].description', "rule 1"),
            JMESPathCheck('[0].properties.rules[0].routes[0].match.prefix', "/1"),
            JMESPathCheck('[0].properties.rules[0].routes[0].action.prefixRewrite', "/"),
            JMESPathCheck('[0].properties.rules[0].targets[0].containerApp', app1),
        ])

        self.cmd(f"az containerapp env http-route-config update -g {resource_group} -n {env_name} -r {route_name} --yaml '{http_route_config2_file_name}'", checks=[
            JMESPathCheck('properties.rules[0].description', "rule 2"),
            JMESPathCheck('properties.rules[0].routes[0].match.prefix', "/2"),
            JMESPathCheck('properties.rules[0].routes[0].action.prefixRewrite', "/"),
            JMESPathCheck('properties.rules[0].targets[0].containerApp', app2),
        ])

        self.cmd(f"az containerapp env http-route-config show -g {resource_group} -n {env_name} -r {route_name}", checks=[
            JMESPathCheck('properties.rules[0].description', "rule 2"),
            JMESPathCheck('properties.rules[0].routes[0].match.prefix', "/2"),
            JMESPathCheck('properties.rules[0].routes[0].action.prefixRewrite', "/"),
            JMESPathCheck('properties.rules[0].targets[0].containerApp', app2),
        ])

        self.cmd(f"az containerapp env http-route-config delete -g {resource_group} -n {env_name} -r {route_name} -y")

        self.cmd(f"az containerapp env http-route-config list -g {resource_group} -n {env_name}", checks=[
            JMESPathCheck('length(@)', 0),
        ])

        self.cmd(f'containerapp delete -g {resource_group} -n {app1} -y')
        self.cmd(f'containerapp delete -g {resource_group} -n {app2} -y')
        self.cmd(f'containerapp env delete -g {resource_group} -n {env_name} -y')

        clean_up_test_file(http_route_config1_file_name)
        clean_up_test_file(http_route_config2_file_name)
        clean_up_test_file(containerapp_file_name)
