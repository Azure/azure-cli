# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest, record_only
from .afdx_scenario_mixin import CdnAfdScenarioMixin

from azure.core.exceptions import (HttpResponseError)


# This tests relies on a specific subscription with existing resources
class CdnAfdSecretScenarioTest(CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_afd_secret_specific_version_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.afd_secret_list_cmd(resource_group, profile_name, expect_failure=True)

        # Create a standard Azure frontdoor profile
        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

        # Create a secret with expired certificate
        secret_name = self.create_random_name(prefix='secret', length=24)
        secret_source = "/subscriptions/3c0124f9-e564-4c42-86f7-fa79457aedc3/resourceGroups/byoc/providers/Microsoft.KeyVault/vaults/Azure-CDN-BYOC/secrets/afde2e-root-azfdtest-xyz"
        secret_version = "31c11b17a98f464b875c322ccc58a9a4"

        with self.assertRaisesRegex(HttpResponseError, "The server \\(leaf\\) certificate isn't within the validity period"):
            self.afd_secret_create_cmd(resource_group,
                                       profile_name,
                                       secret_name,
                                       secret_source,
                                       use_latest_version=False,
                                       secret_version=secret_version)

        secret_version = "341da32dcfec4b4cb3f3f3a410ca7a13"
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_secret_create_cmd(resource_group,
                                   profile_name,
                                   secret_name,
                                   secret_source,
                                   use_latest_version=False,
                                   secret_version=secret_version,
                                   checks=checks)

        show_checks = [JMESPathCheck('name', secret_name),
                       JMESPathCheck('provisioningState', 'Succeeded'),
                       JMESPathCheck('parameters.type', 'CustomerCertificate'),
                       JMESPathCheck('parameters.secretVersion', secret_version),
                       JMESPathCheck('parameters.useLatestVersion', False)]
        self.afd_secret_show_cmd(resource_group, profile_name, secret_name, checks=show_checks)

        list_checks = [JMESPathCheck('length(@)', 1),
                       JMESPathCheck('@[0].name', secret_name),
                       JMESPathCheck('@[0].provisioningState', 'Succeeded')]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

        # Delete the secret
        self.afd_secret_delete_cmd(resource_group, profile_name, secret_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_afd_secret_latest_version_crud(self, resource_group):
        # Create a standard Azure frontdoor profile
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

        # Create a secret
        secret_name = self.create_random_name(prefix='secret', length=24)
        secret_source = "/subscriptions/3c0124f9-e564-4c42-86f7-fa79457aedc3/resourceGroups/byoc/providers/Microsoft.KeyVault/vaults/Azure-CDN-BYOC/secrets/afde2e-root-azfdtest-xyz"
        latest_version = "341da32dcfec4b4cb3f3f3a410ca7a13"
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]
        self.afd_secret_create_cmd(resource_group,
                                   profile_name,
                                   secret_name,
                                   secret_source,
                                   use_latest_version=True,
                                   secret_version=None,
                                   checks=checks)

        show_checks = [JMESPathCheck('name', secret_name),
                       JMESPathCheck('provisioningState', 'Succeeded'),
                       JMESPathCheck('parameters.type', 'CustomerCertificate'),
                       JMESPathCheck('parameters.secretVersion', latest_version),
                       JMESPathCheck('parameters.useLatestVersion', True)]
        self.afd_secret_show_cmd(resource_group, profile_name, secret_name, checks=show_checks)

        # Delete the secret
        self.afd_secret_delete_cmd(resource_group, profile_name, secret_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)
