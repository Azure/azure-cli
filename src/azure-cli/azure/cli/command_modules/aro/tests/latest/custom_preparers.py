# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.preparers import RoleBasedServicePrincipalPreparer
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload
from azure.cli.testsdk.utilities import GraphClientPasswordReplacer
from azure.mgmt.core.tools import resource_id

MOCK_GUID = '00000000-0000-0000-0000-000000000001'
MOCK_SECRET = 'fake-secret'


class AROClusterServicePrincipalPreparer(RoleBasedServicePrincipalPreparer):
    def __init__(
        self,
        name_prefix="clitest",
        skip_assignment=True,
        parameter_name="client_id",
        parameter_password="client_secret",
        dev_setting_sp_name="AZURE_CLI_TEST_DEV_SP_NAME",
        dev_setting_sp_password="AZURE_CLI_TEST_DEV_SP_PASSWORD",
        key="aro_csp",
    ):
        super(AROClusterServicePrincipalPreparer, self).__init__(
            name_prefix,
            skip_assignment,
            parameter_name,
            parameter_password,
            dev_setting_sp_name,
            dev_setting_sp_password,
            key,
        )
        self.client_id_to_replace = None
        self.client_secret_to_replace = None

    def create_resource(self, name, **kwargs):
        client_id, client_secret = self._get_csp_credentials(name)

        self.test_class_instance.kwargs[self.key] = client_id
        self.test_class_instance.kwargs["{}_pass".format(self.key)] = client_secret

        return {
            self.parameter_name: client_id,
            self.parameter_password: client_secret,
        }

    # Overriden because RoleBasedServicePrincipal.remove_resource does not delete
    # the underlying AAD application generated when creating the service principal
    def remove_resource(self, name, **kwargs):
        super().remove_resource(name, **kwargs)

        if not self.dev_setting_sp_name:
            self.live_only_execute(self.cli_ctx, 'az ad app delete --id {}'.format(self.result.get('appId')))

    def process_request(self, request):
        if self.client_id_to_replace in request.uri:
            request.uri = request.uri.replace(self.client_id_to_replace, MOCK_GUID)

        if is_text_payload(request) and isinstance(request.body, bytes):
            request.body = self._replace_byte_keys(request.body)
        elif is_text_payload(request) and isinstance(request.body, str):
            request.body = self._replace_string_keys(request.body)

        return request

    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._replace_string_keys(response['body']['string'])

        return response

    def _get_csp_credentials(self, name):
        if not self.live_test and not self.test_class_instance.in_recording:
            return MOCK_GUID, MOCK_SECRET

        client_id, client_secret = self._generate_csp(name)

        # call AbstractPreparer.moniker to make resource counts and self.resource_moniker consistent between live
        # and play-back. see SingleValueReplacer.process_request, AbstractPreparer.__call__._preparer_wrapper
        # and ScenarioTest.create_random_name. This is so that when self.create_random_name is called for the
        # first time during live or playback, it would have the same value.
        # In short, the default sp preparer in live mode does not call moniker, which leads to inconsistent counts.
        _ = self.moniker

        self.client_id_to_replace = client_id
        self.client_secret_to_replace = client_secret

        return client_id, client_secret

    def _generate_csp(self, name):
        if self.dev_setting_sp_name:
            client_id = self.dev_setting_sp_name
            client_secret = self.dev_setting_sp_password

            return client_id, client_secret

        subscription = self.test_class_instance.get_subscription_id()
        resource_group = self.test_class_instance.kwargs.get('rg')
        command = 'az ad sp create-for-rbac -n {} --role contributor --scopes "{}"'\
            .format(name, resource_id(subscription=subscription, resource_group=resource_group))

        try:
            self.result = self.live_only_execute(self.cli_ctx, command).get_output_in_json()
        except AttributeError:
            pass

        client_id = self.result['appId']
        client_secret = self.result.get('password') or GraphClientPasswordReplacer.PWD_REPLACEMENT

        return client_id, client_secret

    def _replace_string_keys(self, val):
        if self.client_id_to_replace is None:
            return val

        return val.replace(self.client_id_to_replace, MOCK_GUID).replace(self.client_secret_to_replace, MOCK_SECRET)

    def _replace_byte_keys(self, val):
        return self._replace_string_keys(val.decode('utf-8')).encode('utf-8')
