# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)

from .common import TEST_LOCATION
from .utils import prepare_containerapp_env_for_app_e2e_tests


# flake8: noqa
# noqa
# pylint: skip-file


class ContainerAppAuthTest(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_containerapp_auth_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd('containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(resource_group, app, env_id))

        client_id = 'abc123'
        test_secret = 'abc123'
        issuer = 'https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/'

        self.cmd(
            'containerapp auth microsoft update -g {} --name {} --client-id {} --client-secret {} --issuer {} --yes'
            .format(resource_group, app, client_id, test_secret, issuer), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "microsoft-provider-authentication-secret"),
                JMESPathCheck('registration.openIdIssuer', issuer),
            ])

        self.cmd('containerapp auth microsoft show -g {} --name {}'.format(resource_group, app), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "microsoft-provider-authentication-secret"),
                JMESPathCheck('registration.openIdIssuer', issuer),
            ])

        self.cmd('containerapp secret list -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', "microsoft-provider-authentication-secret")
        ])

        self.cmd('containerapp auth show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
        ])

        sas_url = "sasurl"
        self.cmd('containerapp auth update  -g {} -n {} --unauthenticated-client-action AllowAnonymous --token-store true --sas-url-secret {} --yes'.format(resource_group, app, sas_url), checks=[
            JMESPathCheck('name', "current"),
            JMESPathCheck('properties.globalValidation.unauthenticatedClientAction', "AllowAnonymous"),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
            JMESPathCheck('properties.login.tokenStore.enabled', True),
            JMESPathCheck('properties.login.tokenStore.azureBlobStorage.sasUrlSettingName',
                          "blob-storage-token-store-sasurl-secret"),
        ])

        self.cmd("az containerapp secret list --resource-group {} --name {}".format(resource_group, app), checks=[
            JMESPathCheck('length(@)', 2),
        ])

        self.cmd('containerapp auth show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('globalValidation.unauthenticatedClientAction', "AllowAnonymous"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
            JMESPathCheck('login.tokenStore.enabled', True),
            JMESPathCheck('login.tokenStore.azureBlobStorage.sasUrlSettingName',
                          "blob-storage-token-store-sasurl-secret"),
        ])
        login_paramters = 'identityProviders.azureActiveDirectory.login.loginParameters=[a,scope=openid offline_access api://<back-end-client-id>/user_impersonation]'
        self.cmd("containerapp auth update -g {} -n {} --proxy-convention Standard --redirect-provider Facebook --unauthenticated-client-action AllowAnonymous --set '{}'".format(
                resource_group, app, login_paramters), checks=[
                JMESPathCheck('name', 'current'),
                JMESPathCheck('properties.httpSettings.forwardProxy.convention', 'Standard'),
                JMESPathCheck('properties.globalValidation.redirectToProvider', 'Facebook'),
                JMESPathCheck('properties.globalValidation.unauthenticatedClientAction', 'AllowAnonymous'),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientId', client_id),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientSecretSettingName', "microsoft-provider-authentication-secret"),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
                JMESPathCheck('length(properties.identityProviders.azureActiveDirectory.login.loginParameters)', 2),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.login.loginParameters[0]', "a"),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.login.loginParameters[1]', "scope=openid offline_access api://<back-end-client-id>/user_impersonation"),
        ])

        self.cmd('containerapp show  -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded")
        ])

        self.cmd('containerapp auth microsoft update -g {} --name {} --client-id {} --client-secret {} --client-secret-name {} --san a --thumbprint a --issuer {} --allowed-audiences a --tenant-id a --yes'
                 .format(resource_group, app, client_id, test_secret, test_secret, issuer), expect_failure=True)

        self.cmd('containerapp auth update -g {} --name {} --config-file-path a --custom-host-header b --set a --custom-proto-header c --enabled true --excluded-paths b --proxy-convention NoProxy --redirect-provider c --require-https false --runtime-version 0.0.0 '.format(resource_group, app), expect_failure=True)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_containerapp_auth_facebook_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        app_id = 'abc123'
        test_secret = 'abc123'
        issuer = 'https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/'

        self.cmd(
            'containerapp auth facebook update  -g {} --name {} --app-id {} --app-secret {} --graph-api-version 0.0.2 --scopes cc --yes'
            .format(resource_group, app, app_id, test_secret, issuer).format(resource_group, app), checks=[
                JMESPathCheck('graphApiVersion', "0.0.2"),
                JMESPathCheck('login.scopes[0]', "cc"),
                JMESPathCheck('registration.appId', app_id),
                JMESPathCheck('registration.appSecretSettingName', "facebook-provider-authentication-secret"),
            ])
        self.cmd(
            'containerapp auth facebook show  -g {} --name {}'
            .format(resource_group, app), checks=[
                JMESPathCheck('graphApiVersion', "0.0.2"),
                JMESPathCheck('login.scopes[0]', "cc"),
                JMESPathCheck('registration.appId', app_id),
                JMESPathCheck('registration.appSecretSettingName', "facebook-provider-authentication-secret"),
            ])

        self.cmd(
            'containerapp auth facebook update  -g {} --name {} --app-id {} --app-secret-name {} --graph-api-version 0.0.2 --scopes cc --yes'
            .format(resource_group, app, app_id, test_secret, issuer).format(resource_group, app), expect_failure=True)

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_containerapp_auth_github_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        client_id = 'abc123'
        test_secret = 'abc123'
        # github
        self.cmd(
            'containerapp auth github update -g {} --name {} --client-id {} --client-secret {} --yes'
            .format(resource_group, app, client_id, test_secret), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "github-provider-authentication-secret"),
            ])

        self.cmd('containerapp auth github show -g {} --name {}'.format(resource_group, app), checks=[
            JMESPathCheck('registration.clientId', client_id),
            JMESPathCheck('registration.clientSecretSettingName',
                          "github-provider-authentication-secret"),
        ])

        # google
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        self.cmd(
            'containerapp auth google update -g {} --name {} --client-id {} --client-secret {} --yes'
            .format(resource_group, app, client_id, test_secret), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "google-provider-authentication-secret"),
            ])

        self.cmd('containerapp auth google show -g {} --name {}'.format(resource_group, app), checks=[
            JMESPathCheck('registration.clientId', client_id),
            JMESPathCheck('registration.clientSecretSettingName',
                          "google-provider-authentication-secret"),
        ])
        # apple
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        self.cmd(
            'containerapp auth apple update -g {} --name {} --client-id {} --client-secret {} --yes'
            .format(resource_group, app, client_id, test_secret), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "apple-provider-authentication-secret"),
            ])

        self.cmd('containerapp auth apple show -g {} --name {}'.format(resource_group, app), checks=[
            JMESPathCheck('registration.clientId', client_id),
            JMESPathCheck('registration.clientSecretSettingName',
                          "apple-provider-authentication-secret"),
        ])
        # twitter
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        self.cmd(
            'containerapp auth twitter update -g {} --name {} --consumer-key {} --consumer-secret {} --yes'
            .format(resource_group, app, client_id, test_secret), checks=[
                JMESPathCheck('registration.consumerKey', client_id),
                JMESPathCheck('registration.consumerSecretSettingName',
                              "twitter-provider-authentication-secret"),
            ])

        self.cmd('containerapp auth twitter show -g {} --name {}'.format(resource_group, app), checks=[
            JMESPathCheck('registration.consumerKey', client_id),
            JMESPathCheck('registration.consumerSecretSettingName',
                          "twitter-provider-authentication-secret"),
        ])

        self.cmd(
            'containerapp auth twitter update -g {} --name {} --consumer-key {} --consumer-secret-name {} --yes'
            .format(resource_group, app, client_id, test_secret), expect_failure=True)


    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_containerapp_auth_openid_connect_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        env_id = prepare_containerapp_env_for_app_e2e_tests(self)

        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        client_id = 'abc123'
        test_secret = 'abc123'

        # openid-connect
        app = self.create_random_name(prefix='containerapp-auth', length=24)
        self.cmd(
            'containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(
                resource_group, app, env_id))

        provider_name = "customopenid"
        configuration = "test-openid-configuration"
        self.cmd(
            'containerapp auth openid-connect add -g {} --name {} --client-id {} --provider-name {} --openid-configuration {} --scope sc --yes'
            .format(resource_group, app, client_id, provider_name, configuration), checks=[
            JMESPathCheck('registration.clientId', client_id),
            JMESPathCheck('registration.openIdConnectConfiguration.wellKnownOpenIdConfiguration', configuration),
        ])

        self.cmd('containerapp auth openid-connect show -g {} --name {} --provider-name {}'.format(resource_group, app, provider_name), expect_failure=False)
        self.cmd( 'containerapp auth openid-connect remove -g {} --name {} --provider-name {} --yes'.format(resource_group, app, provider_name), expect_failure=False)
        self.cmd('containerapp auth openid-connect update -g {} --name {} --client-id {} --client-secret {} --client-secret-name {} --provider-name {} --openid-configuration {} --scope sc --yes'
            .format(resource_group, app, client_id, test_secret, test_secret, provider_name, configuration), expect_failure=True)
