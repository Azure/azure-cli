# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)
from azure.cli.command_modules.security.tests.latest.common import (SECURITYCONNECTORS_LOCATION)

class SecurityConnectorsTests(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=False, **kwargs)

    @ResourceGroupPreparer(location=SECURITYCONNECTORS_LOCATION)
    def test_security_securityconnectors(self, resource_group):
        name = self.create_random_name(prefix='cli', length=12)
        env_name = 'AzureDevOps'
        hierarchy_identifier = "530aee27-8996-4a9e-a980-336a04985747"

        self.cmd("az security security-connectors create --location {} --resource-group {} --security-connector-name {} --hierarchy-identifier {} --environment-name {} --environment-data azuredevops-scope='' --offerings [0].cspm-monitor-azuredevops=''".format(SECURITYCONNECTORS_LOCATION, resource_group, name, hierarchy_identifier, env_name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('environmentName', env_name),
            JMESPathCheck('environmentData.environmentType', env_name + "Scope")
        ])

        self.cmd("az security security-connectors show --resource-group {} --name {}".format(resource_group, name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('environmentName', env_name),
            JMESPathCheck('environmentData.environmentType', env_name + "Scope")
        ])

        self.cmd("az security security-connectors update --resource-group {} --name {} --environment-name {} --environment-data azuredevops-scope='' --offerings [0].cspm-monitor-azuredevops=''".format(resource_group, name, env_name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('environmentName', env_name),
            JMESPathCheck('environmentData.environmentType', env_name + "Scope")
        ])

        nexttoken = base64.b64encode('{"next_link": null, "offset": 0}'.encode()).decode()
        connectors = self.cmd("az security security-connectors list -g {} --max-items 1 --next-token {}".format(resource_group, nexttoken)).get_output_in_json()
        assert len(connectors) > 0

        self.cmd("az security security-connectors delete --yes --resource-group {} --name {}".format(resource_group, name))