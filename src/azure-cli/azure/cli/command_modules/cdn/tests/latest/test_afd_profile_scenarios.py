# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnAfdProfileScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    def test_afd_profile_crud(self, resource_group):
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_profile_list_cmd(resource_group, checks=list_checks)

        profile_name = self.create_random_name(prefix='profile', length=24)

        tags = 'tag1=value1 tag2=value2'
        self.afd_profile_create_cmd(resource_group, profile_name, tags=tags, options="--origin-response-timeout-seconds 100")

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].location', "Global"),
                       JMESPathCheck('@[0].sku.name', 'Standard_AzureFrontDoor'),
                       JMESPathCheck('@[0].tags.tag1', 'value1'),
                       JMESPathCheck('@[0].tags.tag2', 'value2'),
                       JMESPathCheck('@[0].originResponseTimeoutSeconds', 100)]
        self.afd_profile_list_cmd(resource_group, checks=list_checks)

        show_checks = [JMESPathCheck('location', "Global"),
                       JMESPathCheck('sku.name', 'Standard_AzureFrontDoor'),
                       JMESPathCheck('length(tags)', 2),
                       JMESPathCheck('tags.tag1', 'value1'),
                       JMESPathCheck('tags.tag2', 'value2'),
                       JMESPathCheck('originResponseTimeoutSeconds', 100)]
        self.afd_profile_show_cmd(resource_group,
                                  profile_name,
                                  checks=show_checks)

        update_checks = [JMESPathCheck('location', "Global"),
                         JMESPathCheck('sku.name', 'Standard_AzureFrontDoor'),
                         JMESPathCheck('tags.tag1', None),
                         JMESPathCheck('tags.tag2', None),
                         JMESPathCheck('tags.tag3', 'value3'),
                         JMESPathCheck('tags.tag4', 'value4'),
                         JMESPathCheck('originResponseTimeoutSeconds', 100)]
        tags = 'tag3=value3 tag4=value4'
        self.afd_profile_update_cmd(resource_group,
                                    profile_name,
                                    tags=tags,
                                    checks=update_checks)

        update_checks = [JMESPathCheck('location', "Global"),
                         JMESPathCheck('sku.name', 'Standard_AzureFrontDoor'),
                         JMESPathCheck('tags.tag1', None),
                         JMESPathCheck('tags.tag2', None),
                         JMESPathCheck('tags.tag3', 'value3'),
                         JMESPathCheck('tags.tag4', 'value4'),
                         JMESPathCheck('originResponseTimeoutSeconds', 30)]
        self.afd_profile_update_cmd(resource_group,
                                    profile_name,
                                    options='--origin-response-timeout-seconds 30',
                                    checks=update_checks)

        usage_checks = [JMESPathCheck('length(@)', 6)]
        self.cmd(f"afd profile usage -g {resource_group} --profile-name {profile_name}", checks=usage_checks)

        self.afd_profile_delete_cmd(resource_group, profile_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_profile_list_cmd(resource_group, checks=list_checks)
