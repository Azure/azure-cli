# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import ResourceGroupPreparer, KeyVaultPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from .scenario_mixin import CdnScenarioMixin
from azure.mgmt.cdn.models import (SkuName)

from azure.core.exceptions import (HttpResponseError, ResourceNotFoundError, ResourceExistsError)
from knack.util import CLIError


class CdnCustomDomainScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cdn_domain', additional_tags={'owner': 'jingnanxu'})
    def test_cdn_custom_domain_errors(self, resource_group):
        self.kwargs.update({
            'profile': 'cdnprofile1',
            'endpoint': self.create_random_name(prefix='endpoint', length=24),
            'origin': 'www.test.com',
            'hostname': 'www.contoso.com',
            'name': 'customdomain1',
            'rg': resource_group,
        })

        self.cmd('cdn profile create -g {rg} -n {profile} --sku Standard_Microsoft')
        self.cmd('cdn endpoint create -g {rg} --origin {origin} --profile-name {profile} -n {endpoint}')
        self.cmd('cdn custom-domain list -g {rg} --endpoint-name {endpoint} --profile-name {profile}')

        # These will all fail because we don't really have the ability to create the custom endpoint in test.
        # but they should still fail if there was a CLI-level regression.
        with self.assertRaises(HttpResponseError):
            self.cmd(
                'cdn custom-domain create -g {rg} --endpoint-name {endpoint} --hostname {hostname} --profile-name {profile} -n {name}')
        with self.assertRaises(ResourceNotFoundError):  # exits with code 3 due to missing resource
            self.cmd('cdn custom-domain show -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        # self.cmd('cdn custom-domain delete -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name} --yes')
        with self.assertRaises(ResourceNotFoundError):
            self.cmd(
                'cdn custom-domain enable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')

        with self.assertRaises(CLIError):
            self.cmd(
                'cdn custom-domain disable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_cdn_custom_domain_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku="Standard_Microsoft")
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'aaz-09-01-crud'
        origin = 'www.microsoft1.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.custom_domain_list_cmd(resource_group, profile_name, endpoint_name, checks=list_checks)

        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.aaz0901.clitest.azfdtest.xyz'
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]

        self.custom_domain_create_cmd(group=resource_group,
                                      profile_name=profile_name,
                                      endpoint_name=endpoint_name,
                                      name=custom_domain_name,
                                      hostname=hostname,
                                      checks=checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.custom_domain_list_cmd(resource_group, profile_name, endpoint_name, checks=list_checks)

        self.custom_domain_delete_cmd(resource_group, profile_name, endpoint_name, custom_domain_name)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.custom_domain_list_cmd(resource_group, profile_name, endpoint_name, checks=list_checks)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_cdn_custom_domain_https_verizon(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_verizon.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'aaz-09-01-verizon'
        origin = 'www.microsoft1.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.aaz0901-verizon.clitest.azfdtest.xyz'
        # # Use alternate hostnames for dogfood.
        # if '.azureedge-test.net' in endpoint['hostName']:
        #     hostname = custom_domain_name + '.aaz0901-verizon-fd.clitest.azfdtest.xyz'
        self.custom_domain_create_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, hostname)

        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        self.custom_domain_show_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, checks=checks)

        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsProvisioningState', 'Enabling'),
                  JMESPathCheck('customHttpsProvisioningSubstate', 'SubmittingDomainControlValidationRequest')]
        self.custom_domain_enable_https_command(resource_group,
                                                profile_name,
                                                endpoint_name,
                                                custom_domain_name,
                                                min_tls_version='None',
                                                checks=checks)

        self.custom_domain_disable_https_cmd(resource_group, profile_name, endpoint_name, custom_domain_name)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    # need to switch to a different subscription 3c0124f9-e564-4c42-86f7-fa79457aedc3
    # @KeyVaultPreparer(location='centralus', name_prefix='cdncli-byoc', name_len=24)
    def test_cdn_custom_domain_https_msft(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_microsoft.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'aaz-byoc-6'
        origin = 'www.microsoft1.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        # Create custom domains for CDN managed cert and BYOC
        custom_domain_name = "msft-c"
        byoc_custom_domain_name = "msft-b"
        hostname = custom_domain_name + '-aaz0901.afdx-rp-platform-test.azfdtest.xyz'
        byoc_hostname = byoc_custom_domain_name + '-aaz0901.afdx-rp-platform-test.azfdtest.xyz'
        # # Use alternate hostnames for dogfood.
        # if '.azureedge-test.net' in endpoint['hostName']:
        #     hostname = custom_domain_name + '.aaz0901-byoc-fd.clitest.azfdtest.xyz'
        #     byoc_hostname = byoc_custom_domain_name + '.aaz0901-byoc-fd.clitest.azfdtest.xyz'
        self.custom_domain_create_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, hostname)
        self.custom_domain_create_cmd(resource_group, profile_name, endpoint_name, byoc_custom_domain_name, byoc_hostname)

        # Verify the created custom domains don't have custom HTTPS enabled
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        self.custom_domain_show_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, checks=checks)
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        self.custom_domain_show_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, checks=checks)

        # Enable custom HTTPS with a CDN managed certificate.
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsProvisioningState', 'Enabling'),
                  JMESPathCheck('customHttpsProvisioningSubstate', 'SubmittingDomainControlValidationRequest')]
        self.custom_domain_enable_https_command(resource_group,
                                                profile_name,
                                                endpoint_name,
                                                custom_domain_name,
                                                min_tls_version='1.2',
                                                checks=checks)

        version = "634c38a587884de4980f1b8c1c368712"

        # Enable custom HTTPS with a custom certificate
        # With the latest service side change to move the certificate validation to RP layer, the request will be rejected.
        # with self.assertRaisesRegex(HttpResponseError, "The certificate chain includes an invalid number of certificates. The number of certificates should be greater than 2"):
        self.custom_domain_enable_https_command(resource_group,
                                                profile_name,
                                                endpoint_name,
                                                byoc_custom_domain_name,
                                                user_cert_subscription_id="3c0124f9-e564-4c42-86f7-fa79457aedc3",
                                                user_cert_group_name="byoc",
                                                user_cert_vault_name="AZURE-CDN-BYOC",
                                                user_cert_secret_name="wildcard-afdx-rp-platform-test-azfdtest-xyz",
                                                user_cert_secret_version=version,
                                                user_cert_protocol_type='sni')

    #@unittest.skip("Duplicate cdn endpoint name, cannot rerun live.")
    # need to switch to a different subscription 3c0124f9-e564-4c42-86f7-fa79457aedc3
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    # @KeyVaultPreparer(location='centralus', name_prefix='cdnclibyoc-latest', name_len=24)
    def test_cdn_custom_domain_byoc_latest(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_microsoft.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'aaz-byoc-4'
        origin = 'www.microsoft1.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        # Create custom domain for BYOC
        custom_domain_name = "byoc-c"
        hostname = custom_domain_name + '-aaz0901.afdx-rp-platform-test.azfdtest.xyz'
        # # Use alternate hostname for dogfood.
        # if '.azureedge-test.net' in endpoint['hostName']:
        #     hostname = custom_domain_name + '.aaz-5-df.clitest.azfdtest.xyz'
        self.custom_domain_create_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, hostname)

        # Verify the created custom domain doesn't have custom HTTPS enabled.
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        self.custom_domain_show_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, checks=checks)

        # Enable custom HTTPS with the custom certificate.
        # With the latest service side change to move the certificate validation to RP layer, the request will be rejected.
        # with self.assertRaisesRegex(HttpResponseError, "The certificate chain includes an invalid number of certificates. The number of certificates should be greater than 2"):
        self.custom_domain_enable_https_command(resource_group,
                                                profile_name,
                                                endpoint_name,
                                                custom_domain_name,
                                                user_cert_subscription_id="3c0124f9-e564-4c42-86f7-fa79457aedc3",
                                                user_cert_group_name="byoc",
                                                user_cert_vault_name="AZURE-CDN-BYOC",
                                                user_cert_secret_name="wildcard-afdx-rp-platform-test-azfdtest-xyz",
                                                user_cert_protocol_type='sni')
