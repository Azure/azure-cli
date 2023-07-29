# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)

from .common import TEST_LOCATION
from .utils import create_containerapp_env


class ContainerAppAuthTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_containerapp_auth_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))
        env = self.create_random_name(prefix='containerapp-env', length=24)
        app = self.create_random_name(prefix='containerapp-auth', length=24)

        create_containerapp_env(self, env, resource_group)

        self.cmd('containerapp create -g {} -n {} --environment {} --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80'.format(resource_group, app, env))

        client_id = 'c0d23eb5-ea9f-4a4d-9519-bfa0a422c491'
        client_secret = 'c0d23eb5-ea9f-4a4d-9519-bfa0a422c491'
        issuer = 'https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/'

        self.cmd(
            'containerapp auth microsoft update  -g {} --name {} --client-id {} --client-secret {} --issuer {} --yes'
            .format(resource_group, app, client_id, client_secret, issuer), checks=[
                JMESPathCheck('registration.clientId', client_id),
                JMESPathCheck('registration.clientSecretSettingName',
                              "microsoft-provider-authentication-secret"),
                JMESPathCheck('registration.openIdIssuer', issuer),
            ])

        self.cmd('containerapp secret list -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', "microsoft-provider-authentication-secret")
        ])

        self.cmd('containerapp auth show  -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
        ])

        self.cmd('containerapp auth update  -g {} -n {} --unauthenticated-client-action AllowAnonymous'.format(resource_group, app), checks=[
            JMESPathCheck('name', "current"),
            JMESPathCheck('properties.globalValidation.unauthenticatedClientAction', "AllowAnonymous"),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
        ])

        self.cmd('containerapp auth show  -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('globalValidation.unauthenticatedClientAction', "AllowAnonymous"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientId', client_id),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.clientSecretSettingName',
                          "microsoft-provider-authentication-secret"),
            JMESPathCheck('identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
        ])

        self.cmd('containerapp auth update -g {} -n {} --proxy-convention Standard --redirect-provider Facebook --unauthenticated-client-action AllowAnonymous'.format(
                resource_group, app), checks=[
                JMESPathCheck('name', 'current'),
                JMESPathCheck('properties.httpSettings.forwardProxy.convention', 'Standard'),
                JMESPathCheck('properties.globalValidation.redirectToProvider', 'Facebook'),
                JMESPathCheck('properties.globalValidation.unauthenticatedClientAction', 'AllowAnonymous'),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientId', client_id),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.clientSecretSettingName', "microsoft-provider-authentication-secret"),
                JMESPathCheck('properties.identityProviders.azureActiveDirectory.registration.openIdIssuer', issuer),
            ])

        self.cmd('containerapp show  -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.provisioningState', "Succeeded")
        ])
