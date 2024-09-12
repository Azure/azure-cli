# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)
from azure.cli.command_modules.security.tests.latest.common import (SECURITYCONNECTORS_LOCATION, SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP)

class SecurityConnectorsDevOpsTests(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=False, **kwargs)

    def test_security_securityconnectors_devops_azuredevops(self):
        name = 'dfdsdktests-azdo-01'
        org_name = "dfdsdktests"
        nexttoken = base64.b64encode('{"next_link": null, "offset": 0}'.encode()).decode()

        self.name_replacer

        self.cmd("az security security-connector devops show --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name), checks=[
            JMESPathCheck('properties.autoDiscovery', 'Disabled'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        self.cmd("az security security-connector devops update --resource-group {} --security-connector-name {} --auto-discovery Disabled --inventory-list {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name), checks=[
            JMESPathCheck('properties.autoDiscovery', 'Disabled'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        available_azuredevops = self.cmd("az security security-connector devops list-available-azuredevopsorgs --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name)).get_output_in_json()

        assert len(available_azuredevops) > 0

        onboarded_azuredevops = self.cmd("az security security-connector devops azuredevopsorg list --resource-group {} --security-connector-name {} --max-items 1 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, nexttoken)).get_output_in_json()

        assert len(onboarded_azuredevops) > 0
        assert onboarded_azuredevops[0]['properties']['onboardingState'] == 'Onboarded'
        assert onboarded_azuredevops[0]['properties']['provisioningState'] == 'Succeeded'

        org_name = onboarded_azuredevops[0]['name']

        self.cmd("az security security-connector devops azuredevopsorg show --resource-group {} --security-connector-name {} --org-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        self.cmd("az security security-connector devops azuredevopsorg update --resource-group {} --security-connector-name {} --org-name {} --actionable-remediation state=Enabled category-configurations[0].category=IaC category-configurations[0].minimum-severity-level=High".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name), checks=[
            JMESPathCheck('properties.actionableRemediation.state', 'Enabled'),
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])

        onboarded_projects = self.cmd("az security security-connector devops azuredevopsorg project list --resource-group {} --security-connector-name {} --org-name {} --max-items 5 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, nexttoken)).get_output_in_json()

        assert len(onboarded_projects) > 0
        assert onboarded_projects[0]['properties']['onboardingState'] == 'Onboarded'
        assert onboarded_projects[0]['properties']['provisioningState'] == 'Succeeded'

        project_name = onboarded_projects[0]['name']

        self.cmd("az security security-connector devops azuredevopsorg project show --resource-group {} --security-connector-name {} --org-name {} --project-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, project_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        self.cmd("az security security-connector devops azuredevopsorg project update --resource-group {} --security-connector-name {} --org-name {} --project-name {} --actionable-remediation state=Enabled".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, project_name), checks=[
            JMESPathCheck('properties.actionableRemediation.state', 'Enabled'),
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])

        onboarded_repos = self.cmd("az security security-connector devops azuredevopsorg project repo list --resource-group {} --security-connector-name {} --org-name {} --project-name {} --max-items 5 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, project_name, nexttoken)).get_output_in_json()

        assert len(onboarded_repos) > 0
        assert onboarded_repos[0]['properties']['onboardingState'] == 'Onboarded'
        assert onboarded_repos[0]['properties']['provisioningState'] == 'Succeeded'

        repo_name = onboarded_repos[0]['name']

        self.cmd("az security security-connector devops azuredevopsorg project repo show --resource-group {} --security-connector-name {} --org-name {} --project-name {} --repo-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, project_name, repo_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        self.cmd("az security security-connector devops azuredevopsorg project repo update --resource-group {} --security-connector-name {} --org-name {} --project-name {} --repo-name {} --actionable-remediation state=Enabled".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, org_name, project_name, repo_name), checks=[
            JMESPathCheck('properties.actionableRemediation.state', 'Enabled'),
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])
    
    def test_security_securityconnectors_devops_github(self):
        name = 'dfdsdktests-gh-01'
        nexttoken = base64.b64encode('{"next_link": null, "offset": 0}'.encode()).decode()

        self.cmd("az security security-connector devops show --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name), checks=[
            JMESPathCheck('properties.autoDiscovery', 'Enabled'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        available_githubowners = self.cmd("az security security-connector devops list-available-githubowners --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name)).get_output_in_json()

        assert len(available_githubowners) > 0

        onboarded_githubowners = self.cmd("az security security-connector devops githubowner list --resource-group {} --security-connector-name {} --max-items 1 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, nexttoken)).get_output_in_json()

        assert len(onboarded_githubowners) > 0
        assert onboarded_githubowners[0]['properties']['onboardingState'] == 'Onboarded'

        owner_name = onboarded_githubowners[0]['name']

        self.cmd("az security security-connector devops githubowner show --resource-group {} --security-connector-name {} --owner-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, owner_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])

        onboarded_repos = self.cmd("az security security-connector devops githubowner repo list --resource-group {} --security-connector-name {} --owner-name {} --max-items 5 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, owner_name, nexttoken)).get_output_in_json()

        assert len(onboarded_repos) > 0
        assert onboarded_repos[0]['properties']['onboardingState'] == 'Onboarded'

        repo_name = onboarded_repos[0]['name']

        self.cmd("az security security-connector devops githubowner repo show --resource-group {} --security-connector-name {} --owner-name {} --repo-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, owner_name, repo_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])

    def test_security_securityconnectors_devops_gitlab(self):
        name = 'dfdsdktests-gl-01'
        nexttoken = base64.b64encode('{"next_link": null, "offset": 0}'.encode()).decode()

        self.cmd("az security security-connector devops show --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name), checks=[
            JMESPathCheck('properties.autoDiscovery', 'Disabled'),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])

        available_gitlabgroups = self.cmd("az security security-connector devops list-available-gitlabgroups --resource-group {} --security-connector-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name)).get_output_in_json()

        assert len(available_gitlabgroups) > 0

        onboarded_gitlabgroups = self.cmd("az security security-connector devops gitlabgroup list --resource-group {} --security-connector-name {} --max-items 1 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, nexttoken)).get_output_in_json()

        assert len(onboarded_gitlabgroups) > 0
        assert onboarded_gitlabgroups[0]['properties']['onboardingState'] == 'Onboarded'

        group_name = onboarded_gitlabgroups[0]['name']

        self.cmd("az security security-connector devops gitlabgroup show --resource-group {} --security-connector-name {} --group-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, group_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])

        subgroups = self.cmd("az security security-connector devops gitlabgroup list-subgroups --resource-group {} --security-connector-name {} --group-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, group_name)).get_output_in_json()
        assert len(subgroups) > 0

        onboarded_repos = self.cmd("az security security-connector devops gitlabgroup project list --resource-group {} --security-connector-name {} --group-name {} --max-items 5 --next-token {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, group_name, nexttoken)).get_output_in_json()

        assert len(onboarded_repos) > 0
        assert onboarded_repos[0]['properties']['onboardingState'] == 'Onboarded'

        repo_name = onboarded_repos[0]['name']

        self.cmd("az security security-connector devops gitlabgroup project show --resource-group {} --security-connector-name {} --group-name {} --project-name {}".format(SECURITYCONNECTORS_DEVOPS_RESOURCE_GROUP, name, group_name, repo_name), checks=[
            JMESPathCheck('properties.onboardingState', 'Onboarded')
        ])
    
    @ResourceGroupPreparer(location=SECURITYCONNECTORS_LOCATION)
    def test_security_securityconnectors_devops_create_update(self, resource_group):
        hierarchy_identifier = "3bbc4fce-f6ae-4059-85e5-13e3e02dde7c"
        code = "dummycode"
        org_name = "dfdsdktests"
        name = self.create_random_name(prefix='cli', length=12)
        env_name = 'AzureDevOps'

        self.cmd("az security security-connector create --location {} --resource-group {} --security-connector-name {} --hierarchy-identifier {} --environment-name {} --environment-data azuredevops-scope='' --offerings [0].cspm-monitor-azuredevops=''".format(SECURITYCONNECTORS_LOCATION, resource_group, name, hierarchy_identifier, env_name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('environmentName', env_name),
            JMESPathCheck('environmentData.environmentType', env_name + "Scope")
        ])

        from azure.core.exceptions import HttpResponseError
        with self.assertRaisesRegex(HttpResponseError, expected_regex=".*TokenExchangeFailed.*"):
            self.cmd("az security security-connector devops create --resource-group {} --security-connector-name {} --auto-discovery Disabled --inventory-list {} --authorization-code {}".format(resource_group, name, org_name, code))

        devops = self.cmd("az security security-connector devops show --resource-group {} --security-connector-name {}".format(resource_group, name)).get_output_in_json()

        assert devops is not None
        assert devops['properties']['autoDiscovery'] == 'Disabled'
        assert devops['properties']['provisioningState'] == 'Failed'

        self.cmd("az security security-connector devops delete --yes --resource-group {} --security-connector-name {}".format(resource_group, name))
