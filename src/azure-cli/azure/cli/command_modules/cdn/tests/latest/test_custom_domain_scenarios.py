# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, KeyVaultPreparer, JMESPathCheck
from azure.cli.testsdk import ScenarioTest
from .scenario_mixin import CdnScenarioMixin
from azure.mgmt.cdn.models import (SkuName, CustomHttpsProvisioningState, ProtocolType,
                                   CertificateType)

from azure.core.exceptions import (HttpResponseError)


class CdnCustomDomainScenarioTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cdn_domain')
    def test_cdn_custom_domain_errors(self, resource_group):
        from knack.util import CLIError

        self.kwargs.update({
            'profile': 'cdnprofile1',
            'endpoint': self.create_random_name(prefix='endpoint', length=24),
            'origin': 'www.test.com',
            'hostname': 'www.example.com',
            'name': 'customdomain1',
            'rg': resource_group,
        })

        self.cmd('cdn profile create -g {rg} -n {profile}')
        self.cmd('cdn endpoint create -g {rg} --origin {origin} --profile-name {profile} -n {endpoint}')
        self.cmd('cdn custom-domain list -g {rg} --endpoint-name {endpoint} --profile-name {profile}')

        # These will all fail because we don't really have the ability to create the custom endpoint in test.
        # but they should still fail if there was a CLI-level regression.
        with self.assertRaises(HttpResponseError):
            self.cmd(
                'cdn custom-domain create -g {rg} --endpoint-name {endpoint} --hostname {hostname} --profile-name {profile} -n {name}')
        with self.assertRaises(SystemExit):  # exits with code 3 due to missing resource
            self.cmd('cdn custom-domain show -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        self.cmd('cdn custom-domain delete -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        with self.assertRaises(HttpResponseError):
            self.cmd(
                'cdn custom-domain enable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')
        with self.assertRaises(CLIError):
            self.cmd(
                'cdn custom-domain disable-https -g {rg} --endpoint-name {endpoint} --profile-name {profile} -n {name}')

    @ResourceGroupPreparer()
    def test_cdn_custom_domain_crud(self, resource_group):
        profile_name = self.create_random_name(prefix='profile', length=24)
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_akamai.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'cdn-cli-test'
        origin = 'www.example.com'
        self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin)

        list_checks = [JMESPathCheck('length(@)', 0)]
        self.custom_domain_list_cmd(resource_group, profile_name, endpoint_name, checks=list_checks)

        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.cdn-cli-test.azfdtest.xyz'
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        try:
            self.custom_domain_create_cmd(group=resource_group,
                                          profile_name=profile_name,
                                          endpoint_name=endpoint_name,
                                          name=custom_domain_name,
                                          hostname=hostname,
                                          checks=checks)
        except HttpResponseError as err:
            if err.status_code != 400:
                raise err
            hostname = custom_domain_name + '.cdn-cli-test-dogfood.azfdtest.xyz'
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

    @ResourceGroupPreparer()
    def test_cdn_custom_domain_https_akamai(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_akamai.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'cdn-cli-test-2'
        origin = 'www.example.com'
        endpoint = self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        # Create custom domain
        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.cdn-cli-test-2.azfdtest.xyz'
        # Use alternate hostname for dogfood.
        if '.azureedge-test.net' in endpoint['hostName']:
            hostname = custom_domain_name + '.cdn-cli-test-2-df.azfdtest.xyz'
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
                                                checks=checks)

        with self.assertRaises(HttpResponseError):
            self.custom_domain_disable_https_cmd(resource_group, profile_name, endpoint_name, custom_domain_name)

    @ResourceGroupPreparer()
    def test_cdn_custom_domain_https_verizon(self, resource_group):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_verizon.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'cdn-cli-test-3'
        origin = 'www.contoso.com'
        endpoint = self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.cdn-cli-test-3.azfdtest.xyz'
        # Use alternate hostnames for dogfood.
        if '.azureedge-test.net' in endpoint['hostName']:
            hostname = custom_domain_name + '.cdn-cli-test-3-df.azfdtest.xyz'
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

        with self.assertRaises(HttpResponseError):
            self.custom_domain_disable_https_cmd(resource_group, profile_name, endpoint_name, custom_domain_name)

    @ResourceGroupPreparer()
    @KeyVaultPreparer(location='centralus', name_prefix='cdncli-byoc', name_len=24)
    def test_cdn_custom_domain_https_msft(self, resource_group, key_vault):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_microsoft.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'cdn-cli-test-4'
        origin = 'www.example.com'
        endpoint = self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        # Create custom domains for CDN managed cert and BYOC
        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        byoc_custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.cdn-cli-test-4.azfdtest.xyz'
        byoc_hostname = byoc_custom_domain_name + '.cdn-cli-test-4.azfdtest.xyz'
        # Use alternate hostnames for dogfood.
        if '.azureedge-test.net' in endpoint['hostName']:
            hostname = custom_domain_name + '.cdn-cli-test-4-df.azfdtest.xyz'
            byoc_hostname = byoc_custom_domain_name + '.cdn-cli-test-4-df.azfdtest.xyz'
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
                                                min_tls_version='1.0',
                                                checks=checks)

        # Create a TLS cert to use for BYOC.
        cert_name = self.create_random_name(prefix='cert', length=20)
        self.byoc_create_keyvault_cert(key_vault, cert_name)
        # Get and parse the latest version for the certificate.
        versions = self.byoc_get_keyvault_cert_versions(key_vault, cert_name).get_output_in_json()
        version = versions[0]['id'].split('/')[-1]

        # Enable custom HTTPS with a custom certificate
        # With the latest service side change to move the certificate validation to RP layer, the request will be rejected.
        with self.assertRaisesRegexp(HttpResponseError, "The certificate imported from the Key Vault is a Self Signed certificate and is not permitted for Bring Your Own Certificate"):
            self.custom_domain_enable_https_command(resource_group,
                                                    profile_name,
                                                    endpoint_name,
                                                    byoc_custom_domain_name,
                                                    user_cert_subscription_id=self.get_subscription_id(),
                                                    user_cert_group_name=resource_group,
                                                    user_cert_vault_name=key_vault,
                                                    user_cert_secret_name=cert_name,
                                                    user_cert_secret_version=version,
                                                    user_cert_protocol_type='sni')

    @ResourceGroupPreparer()
    @KeyVaultPreparer(location='centralus', name_prefix='cdnclibyoc-latest', name_len=24)
    def test_cdn_custom_domain_byoc_latest(self, resource_group, key_vault):
        profile_name = 'profile123'
        self.endpoint_list_cmd(resource_group, profile_name, expect_failure=True)

        self.profile_create_cmd(resource_group, profile_name, sku=SkuName.standard_microsoft.value)
        # Endpoint name and custom domain hostname are hard-coded because of
        # custom domain CNAME requirement. If test fails to cleanup, the
        # resource group must be manually deleted in order to re-run.
        endpoint_name = 'cdn-cli-test-5'
        origin = 'www.example.com'
        endpoint = self.endpoint_create_cmd(resource_group, endpoint_name, profile_name, origin).get_output_in_json()

        # Create custom domain for BYOC
        custom_domain_name = self.create_random_name(prefix='customdomain', length=20)
        hostname = custom_domain_name + '.cdn-cli-test-5.azfdtest.xyz'
        # Use alternate hostname for dogfood.
        if '.azureedge-test.net' in endpoint['hostName']:
            hostname = custom_domain_name + '.cdn-cli-test-5-df.azfdtest.xyz'
        self.custom_domain_create_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, hostname)

        # Verify the created custom domain doesn't have custom HTTPS enabled.
        checks = [JMESPathCheck('name', custom_domain_name),
                  JMESPathCheck('hostName', hostname),
                  JMESPathCheck('customHttpsParameters', None)]
        self.custom_domain_show_cmd(resource_group, profile_name, endpoint_name, custom_domain_name, checks=checks)

        # Create a TLS cert to use for BYOC.
        cert_name = self.create_random_name(prefix='cert', length=20)
        self.byoc_create_keyvault_cert(key_vault, cert_name)

        # Enable custom HTTPS with the custom certificate.
        # With the latest service side change to move the certificate validation to RP layer, the request will be rejected.
        with self.assertRaisesRegexp(HttpResponseError, "The certificate imported from the Key Vault is a Self Signed certificate and is not permitted for Bring Your Own Certificate"):
            self.custom_domain_enable_https_command(resource_group,
                                                    profile_name,
                                                    endpoint_name,
                                                    custom_domain_name,
                                                    user_cert_subscription_id=self.get_subscription_id(),
                                                    user_cert_group_name=resource_group,
                                                    user_cert_vault_name=key_vault,
                                                    user_cert_secret_name=cert_name,
                                                    user_cert_protocol_type='sni')
