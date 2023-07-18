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
    @ResourceGroupPreparer()
    def test_afd_secret_specific_version_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.afd_secret_list_cmd(resource_group, profile_name, expect_failure=True)

        # Create a standard Azure frontdoor profile
        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

        # Create a secret with expired certificate
        secret_name = self.create_random_name(prefix='secret', length=24)
        secret_source = f"/subscriptions/{self.get_subscription_id()}/resourceGroups/CliDevReservedGroup/providers/Microsoft.KeyVault/vaults/clibyoc-int/secrets/localdev-multi"
        secret_version = "5f652542f6ef46ef9fc4ed8af07c54f1"

        with self.assertRaisesRegexp(HttpResponseError, "The server \\(leaf\\) certificate isn't within the validity period"):
            self.afd_secret_create_cmd(resource_group,
                               profile_name,
                               secret_name,
                               secret_source,
                               use_latest_version=False,
                               secret_version=secret_version)

        secret_version = "255adcc454844929a2f95c2aa3b6c61f"
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

    @ResourceGroupPreparer()
    def test_afd_secret_latest_version_crud(self, resource_group):
        # Create a standard Azure frontdoor profile
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.afd_profile_create_cmd(resource_group, profile_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)

        # Create a secret
        secret_name = self.create_random_name(prefix='secret', length=24)
        secret_source = f"/subscriptions/{self.get_subscription_id()}/resourceGroups/CliDevReservedGroup/providers/Microsoft.KeyVault/vaults/clibyoc-int/secrets/localdev-multi"
        latest_version = "255adcc454844929a2f95c2aa3b6c61f"
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
                       JMESPathCheck('parameters.secretSource.id', secret_source, False),
                       JMESPathCheck('parameters.secretVersion', latest_version),
                       JMESPathCheck('parameters.useLatestVersion', True)]
        self.afd_secret_show_cmd(resource_group, profile_name, secret_name, checks=show_checks)

        # Delete the secret
        self.afd_secret_delete_cmd(resource_group, profile_name, secret_name)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.afd_secret_list_cmd(resource_group, profile_name, checks=list_checks)
