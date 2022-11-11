# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
from knack.util import CLIError

from azure.cli.command_modules.appservice.static_sites import \
    list_staticsites, show_staticsite, delete_staticsite, create_staticsites, disconnect_staticsite, \
    reconnect_staticsite, list_staticsite_environments, show_staticsite_environment, list_staticsite_domains, \
    set_staticsite_domain, delete_staticsite_domain, list_staticsite_functions, list_staticsite_app_settings, \
    set_staticsite_app_settings, delete_staticsite_app_settings, list_staticsite_users, \
    invite_staticsite_users, update_staticsite_users, update_staticsite, list_staticsite_secrets, \
    reset_staticsite_api_key, delete_staticsite_environment, link_user_function, unlink_user_function, get_user_function, \
    assign_identity, remove_identity, show_identity, enable_staticwebapp_enterprise_edge, disable_staticwebapp_enterprise_edge, show_staticwebapp_enterprise_edge_status
from azure.core.exceptions import ResourceNotFoundError


class TestStaticAppCommands(unittest.TestCase):
    def setUp(self):
        _set_up_client_mock(self)
        _set_up_fake_apps(self)

    def test_list_empty_staticapp(self):
        self.staticapp_client.list.return_value = []

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 0)

    def test_list_staticapp_with_resourcegroup(self):
        self.staticapp_client.get_static_sites_by_resource_group.return_value = [self.app1]

        response = list_staticsites(self.mock_cmd, self.rg1)

        self.staticapp_client.get_static_sites_by_resource_group.assert_called_once_with(self.rg1)
        self.assertEqual(len(response), 1)
        self.assertIn(self.app1, response)

    def test_list_staticapp_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 2)
        self.assertIn(self.app1, response)
        self.assertIn(self.app2, response)

    def test_show_staticapp_with_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1

        response = show_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_static_site.assert_called_once_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)

    def test_show_staticapp_without_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = show_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.get_static_site.assert_called_once_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)

    def test_show_staticapp_not_exist(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        with self.assertRaises(CLIError):
            show_staticsite(self.mock_cmd, self.name1_not_exist)

    def test_delete_staticapp_with_resourcegroup(self):
        delete_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.begin_delete_static_site.assert_called_once_with(resource_group_name=self.rg1, name=self.name1)

    def test_delete_staticapp_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        delete_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.begin_delete_static_site.assert_called_once_with(resource_group_name=self.rg1, name=self.name1)

    def test_delete_staticapp_not_exist(self):
        with self.assertRaises(CLIError):
            delete_staticsite(self.mock_cmd, self.name1_not_exist)


    def test_create_staticapp(self):
        from azure.mgmt.web.models import StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription
        self.mock_cmd.get_models.return_value = StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription
        app_location = './src'
        api_location = './api/'
        output_location = '/.git/'
        tags = {'key1': 'value1'}

        with mock.patch("azure.cli.command_modules.appservice.static_sites.show_staticsite", side_effect=[ResourceNotFoundError("msg"), None]):
            create_staticsites(
                self.mock_cmd, self.rg1, self.name1, self.location1,
                self.source1, self.branch1, self.token1,
                app_location=app_location, api_location=api_location, output_location=output_location,
                tags=tags)

        self.staticapp_client.begin_create_or_update_static_site.assert_called_once()
        arg_list = self.staticapp_client.begin_create_or_update_static_site.call_args[1]
        self.assertEqual(self.name1, arg_list["name"])
        self.assertEqual(self.rg1, arg_list["resource_group_name"])
        self.assertEqual(self.location1, arg_list["static_site_envelope"].location)
        self.assertEqual(self.source1, arg_list["static_site_envelope"].repository_url)
        self.assertEqual(self.branch1, arg_list["static_site_envelope"].branch)
        self.assertEqual(tags, arg_list["static_site_envelope"].tags)
        self.assertEqual('Free', arg_list["static_site_envelope"].sku.name)
        self.assertEqual(app_location, arg_list["static_site_envelope"].build_properties.app_location)
        self.assertEqual(api_location, arg_list["static_site_envelope"].build_properties.api_location)
        self.assertEqual(output_location, arg_list["static_site_envelope"].build_properties.app_artifact_location)

        # assert that a duplicate create call doesn't raise an error or call client create method again
        create_staticsites(
            self.mock_cmd, self.rg1, self.name1, self.location1,
            self.source1, self.branch1, self.token1,
            app_location=app_location, api_location=api_location, output_location=output_location,
            tags=tags)
        self.staticapp_client.begin_create_or_update_static_site.assert_called_once()


    def test_create_staticapp_with_standard_sku(self):
        from azure.mgmt.web.models import StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription
        self.mock_cmd.get_models.return_value = StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription

        with mock.patch("azure.cli.command_modules.appservice.static_sites.show_staticsite", side_effect=[ResourceNotFoundError("msg"), None]):
            create_staticsites(
                self.mock_cmd, self.rg1, self.name1, self.location1,
                self.source1, self.branch1, self.token1, sku='standard')

        self.staticapp_client.begin_create_or_update_static_site.assert_called_once()
        arg_list = self.staticapp_client.begin_create_or_update_static_site.call_args[1]
        self.assertEqual('Standard', arg_list["static_site_envelope"].sku.name)

    def test_create_staticapp_missing_token(self):
        app_location = './src'
        api_location = './api/'
        output_location = '/.git/'
        tags = {'key1': 'value1'}

        with self.assertRaises(CLIError):
            with mock.patch("azure.cli.command_modules.appservice.static_sites.show_staticsite", side_effect=ResourceNotFoundError("msg")):
                create_staticsites(
                    self.mock_cmd, self.rg1, self.name1, self.location1,
                    self.source1, self.branch1,
                    app_location=app_location, api_location=api_location, output_location=output_location,
                    tags=tags)

    def test_update_staticapp(self):
        from azure.mgmt.web.models import StaticSiteARMResource, SkuDescription
        self.mock_cmd.get_models.return_value = StaticSiteARMResource, SkuDescription
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]
        tags = {'key1': 'value1'}
        sku = 'Standard'

        update_staticsite(cmd=self.mock_cmd, name=self.name1, source=self.source2, branch=self.branch2, token=self.token2, tags=tags, sku=sku)

        self.staticapp_client.update_static_site.assert_called_once()
        arg_list = self.staticapp_client.update_static_site.call_args[1]
        self.assertEqual(self.name1, arg_list["name"])
        self.assertEqual(self.source2, arg_list["static_site_envelope"].repository_url)
        self.assertEqual(self.branch2, arg_list["static_site_envelope"].branch)
        self.assertEqual(self.token2, arg_list["static_site_envelope"].repository_token)
        self.assertEqual(tags, arg_list["static_site_envelope"].tags)
        self.assertEqual(sku, arg_list["static_site_envelope"].sku.name)

    def test_update_staticapp_with_no_values_passed_in(self):
        from azure.mgmt.web.models import StaticSiteARMResource, SkuDescription
        self.mock_cmd.get_models.return_value = StaticSiteARMResource, SkuDescription
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        update_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.update_static_site.assert_called_once()
        arg_list = self.staticapp_client.update_static_site.call_args[1]
        self.assertEqual(self.name1, arg_list["name"])
        self.assertEqual(self.source1, arg_list["static_site_envelope"].repository_url)
        self.assertEqual(self.branch1, arg_list["static_site_envelope"].branch)
        self.assertEqual(self.token1, arg_list["static_site_envelope"].repository_token)
        self.assertEqual(self.app1.tags, arg_list["static_site_envelope"].tags)
        self.assertEqual('Free', arg_list["static_site_envelope"].sku.name)

    def test_update_staticapp_not_exist(self):
        from azure.mgmt.web.models import StaticSiteARMResource, SkuDescription
        self.mock_cmd.get_models.return_value = StaticSiteARMResource, SkuDescription
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        with self.assertRaises(CLIError):
            update_staticsite(self.mock_cmd, self.name1_not_exist)

    def test_disconnect_staticapp_with_resourcegroup(self):
        disconnect_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.begin_detach_static_site.assert_called_once_with(resource_group_name=self.rg1, name=self.name1)

    def test_disconnect_staticapp_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        disconnect_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.begin_detach_static_site.assert_called_once_with(resource_group_name=self.rg1, name=self.name1)

    @mock.patch('azure.cli.command_modules.appservice.static_sites.create_staticsites', autospec=True)
    def test_reconnect_staticapp_with_resourcegroup(self, create_staticsites_mock):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        reconnect_staticsite(self.mock_cmd, self.name1, self.source1, self.branch1, self.token1,
                             resource_group_name=self.rg1)

        create_staticsites_mock.assert_called_once_with(self.mock_cmd, self.rg1, self.name1, self.location1,
                                                        self.source1, self.branch1, self.token1, login_with_github=False, no_wait=False)

    @mock.patch('azure.cli.command_modules.appservice.static_sites.create_staticsites', autospec=True)
    def test_reconnect_staticapp_without_resourcegroup(self, create_staticsites_mock):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        reconnect_staticsite(self.mock_cmd, self.name1, self.source1, self.branch1, self.token1)

        create_staticsites_mock.assert_called_once_with(self.mock_cmd, self.rg1, self.name1, self.location1,
                                                        self.source1, self.branch1, self.token1, login_with_github=False, no_wait=False)

    def test_list_staticsite_environments_with_resourcegroup(self):
        list_staticsite_environments(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_static_site_builds.assert_called_once_with(self.rg1, self.name1)

    def test_list_staticsite_environments_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        list_staticsite_environments(self.mock_cmd, self.name1)

        self.staticapp_client.get_static_site_builds.assert_called_once_with(self.rg1, self.name1)

    def test_show_staticsite_environment_with_resourcegroup(self):
        show_staticsite_environment(self.mock_cmd, self.name1, self.environment1, self.rg1)

        self.staticapp_client.get_static_site_build.assert_called_once_with(self.rg1, self.name1, self.environment1)

    def test_show_staticsite_environment_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        show_staticsite_environment(self.mock_cmd, self.name1, self.environment1)

        self.staticapp_client.get_static_site_build.assert_called_once_with(self.rg1, self.name1, self.environment1)

    def test_set_staticsite_domain_with_resourcegroup(self):
        set_staticsite_domain(self.mock_cmd, self.name1, self.hostname1, self.rg1)

        self.staticapp_client.begin_validate_custom_domain_can_be_added_to_static_site.assert_called_once_with(
            self.rg1, self.name1, self.hostname1, self.hostname1_validation)
        self.staticapp_client.begin_create_or_update_static_site_custom_domain.assert_called_once_with(
            resource_group_name=self.rg1, name=self.name1, domain_name=self.hostname1,
            static_site_custom_domain_request_properties_envelope=self.hostname1_validation)

    def test_set_staticsite_domain_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        set_staticsite_domain(self.mock_cmd, self.name1, self.hostname1)

        self.staticapp_client.begin_validate_custom_domain_can_be_added_to_static_site.assert_called_once_with(
            self.rg1, self.name1, self.hostname1, self.hostname1_validation)
        self.staticapp_client.begin_create_or_update_static_site_custom_domain.assert_called_once_with(
            resource_group_name=self.rg1, name=self.name1, domain_name=self.hostname1,
            static_site_custom_domain_request_properties_envelope=self.hostname1_validation)

    def test_delete_staticsite_domain_with_resourcegroup(self):
        delete_staticsite_domain(self.mock_cmd, self.name1, self.hostname1, self.rg1)

        self.staticapp_client.begin_delete_static_site_custom_domain.assert_called_once_with(
            resource_group_name=self.rg1, name=self.name1, domain_name=self.hostname1)

    def test_delete_staticsite_domain_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        delete_staticsite_domain(self.mock_cmd, self.name1, self.hostname1)

        self.staticapp_client.begin_delete_static_site_custom_domain.assert_called_once_with(
            resource_group_name=self.rg1, name=self.name1, domain_name=self.hostname1)

    def test_delete_staticsite_environment_with_resourcegroup(self):
        delete_staticsite_environment(self.mock_cmd, self.name1, self.environment1, self.rg1)

        self.staticapp_client.begin_delete_static_site_build.assert_called_once_with(self.rg1, self.name1, self.environment1)

    def test_delete_staticsite_environment_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        delete_staticsite_environment(self.mock_cmd, self.name1, self.environment1)

        self.staticapp_client.begin_delete_static_site_build.assert_called_once_with(self.rg1, self.name1, self.environment1)

    def test_list_staticsite_functions_with_resourcegroup(self):
        list_staticsite_functions(self.mock_cmd, self.name1, self.rg1, self.environment1)

        self.staticapp_client.list_static_site_build_functions.assert_called_once_with(
            self.rg1, self.name1, self.environment1)

    def test_list_staticsite_functions_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        list_staticsite_functions(self.mock_cmd, self.name1, environment_name=self.environment1)

        self.staticapp_client.list_static_site_build_functions.assert_called_once_with(
            self.rg1, self.name1, self.environment1)

    def test_list_staticsite_app_settings_with_resourcegroup(self):
        list_staticsite_app_settings(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.list_static_site_app_settings.assert_called_once_with(
            self.rg1, self.name1)

    def test_list_staticsite_app_settings_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        list_staticsite_app_settings(self.mock_cmd, self.name1)

        self.staticapp_client.list_static_site_app_settings.assert_called_once_with(
            self.rg1, self.name1)

    def test_set_staticsite_app_settings_with_resourcegroup(self):
        from azure.mgmt.web.models import StringDictionary

        app_settings1_input = ['key1=val1', 'key2=val2==', 'key3=val3=']

        self.staticapp_client.list_static_site_app_settings.return_value = StringDictionary(properties={})

        set_staticsite_app_settings(self.mock_cmd, self.name1, app_settings1_input, self.rg1)

        self.staticapp_client.create_or_update_static_site_app_settings.assert_called_once()

    def test_set_staticsite_app_settings_without_resourcegroup(self):
        from azure.mgmt.web.models import StringDictionary

        app_settings1_input = ['key1=val1', 'key2=val2==', 'key3=val3=']
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        self.staticapp_client.list_static_site_app_settings.return_value = StringDictionary(properties={})

        set_staticsite_app_settings(self.mock_cmd, self.name1, app_settings1_input)

        self.staticapp_client.create_or_update_static_site_app_settings.assert_called_once()

    def test_delete_staticsite_app_settings_with_resourcegroup(self):
        # setup
        current_app_settings = {'key1': 'val1', 'key2': 'val2'}
        app_settings_keys_to_delete = ['key1']

        class AppSettings:
            properties = current_app_settings

        self.staticapp_client.list_static_site_app_settings.return_value = AppSettings

        # action
        delete_staticsite_app_settings(self.mock_cmd, self.name1, app_settings_keys_to_delete, self.rg1)

        # validate
        self.staticapp_client.create_or_update_static_site_app_settings.assert_called_once()

    def test_delete_staticsite_app_settings_without_resourcegroup(self):
        # setup
        current_app_settings = {'key1': 'val1', 'key2': 'val2'}
        app_settings_keys_to_delete = ['key1']

        class AppSettings:
            properties = current_app_settings

        self.staticapp_client.list_static_site_app_settings.return_value = AppSettings
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        # action
        delete_staticsite_app_settings(self.mock_cmd, self.name1, app_settings_keys_to_delete)

        # validate
        self.staticapp_client.create_or_update_static_site_app_settings.assert_called_once()

    def test_list_staticsite_users_with_resourcegroup(self):
        authentication_provider = 'GitHub'

        list_staticsite_users(self.mock_cmd, self.name1, self.rg1, authentication_provider=authentication_provider)

        self.staticapp_client.list_static_site_users.assert_called_once_with(
            self.rg1, self.name1, authentication_provider)

    def test_list_staticsite_users_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]
        authentication_provider = 'GitHub'

        list_staticsite_users(self.mock_cmd, self.name1, authentication_provider=authentication_provider)

        self.staticapp_client.list_static_site_users.assert_called_once_with(
            self.rg1, self.name1, authentication_provider)

    def test_invite_staticsite_users_with_resourcegroup(self):
        authentication_provider = 'GitHub'
        user_details = 'JohnDoe'
        roles = 'Contributor,Reviewer'
        invitation_expiration_in_hours = 2
        from azure.mgmt.web.models import StaticSiteUserInvitationRequestResource
        self.mock_cmd.get_models.return_value = StaticSiteUserInvitationRequestResource

        invite_staticsite_users(self.mock_cmd, self.name1, authentication_provider, user_details, self.hostname1,
                                roles, invitation_expiration_in_hours, self.rg1)

        arg_list = self.staticapp_client.create_user_roles_invitation_link.call_args[0]

        self.assertEqual(self.rg1, arg_list[0])
        self.assertEqual(self.name1, arg_list[1])
        self.assertEqual(self.hostname1, arg_list[2].domain)
        self.assertEqual(authentication_provider, arg_list[2].provider)
        self.assertEqual(user_details, arg_list[2].user_details)
        self.assertEqual(invitation_expiration_in_hours, arg_list[2].num_hours_to_expiration)

    def test_invite_staticsite_users_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]
        authentication_provider = 'GitHub'
        user_details = 'JohnDoe'
        roles = 'Contributor,Reviewer'
        invitation_expiration_in_hours = 2
        from azure.mgmt.web.models import StaticSiteUserInvitationRequestResource
        self.mock_cmd.get_models.return_value = StaticSiteUserInvitationRequestResource

        invite_staticsite_users(self.mock_cmd, self.name1, authentication_provider, user_details, self.hostname1,
                                roles, invitation_expiration_in_hours)

        arg_list = self.staticapp_client.create_user_roles_invitation_link.call_args[0]

        self.assertEqual(self.rg1, arg_list[0])
        self.assertEqual(self.name1, arg_list[1])
        self.assertEqual(self.hostname1, arg_list[2].domain)
        self.assertEqual(authentication_provider, arg_list[2].provider)
        self.assertEqual(user_details, arg_list[2].user_details)
        self.assertEqual(invitation_expiration_in_hours, arg_list[2].num_hours_to_expiration)

    def test_update_staticsite_users_with_resourcegroup_with_all_args(self):
        from azure.mgmt.web.models import StaticSiteUserARMResource

        roles = 'Contributor,Reviewer'
        authentication_provider = 'GitHub'
        user_details = 'JohnDoe'
        user_id = 100

        update_staticsite_users(self.mock_cmd, self.name1, roles, authentication_provider=authentication_provider,
                                user_details=user_details, user_id=user_id, resource_group_name=self.rg1)

        self.staticapp_client.update_static_site_user.assert_called_once_with(self.rg1, self.name1,
            authentication_provider, user_id, static_site_user_envelope=StaticSiteUserARMResource(roles=roles))

    def test_update_staticsite_users_with_resourcegroup_without_auth_provider(self):
        from azure.mgmt.web.models import StaticSiteUserARMResource

        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        authentication_provider = 'GitHub'
        user_id = '100'
        _mock_list_users_for_without_auth_provider(self, user_id, authentication_provider, user_details)

        update_staticsite_users(self.mock_cmd, self.name1, roles,
                                user_details=user_details, user_id=user_id, resource_group_name=self.rg1)

        self.staticapp_client.update_static_site_user.assert_called_once_with(self.rg1, self.name1,
            authentication_provider, user_id, static_site_user_envelope=StaticSiteUserARMResource(roles=roles))

    def test_update_staticsite_users_with_resourcegroup_without_auth_provider_user_not_found(self):
        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        user_id = '100'
        _mock_list_users_for_without_auth_provider(self, 'other_user_id',
                                                   'dummy_authentication_provider', 'dummy_user_details')

        with self.assertRaises(CLIError):
            update_staticsite_users(self.mock_cmd, self.name1, roles,
                                    user_details=user_details, user_id=user_id, resource_group_name=self.rg1)

    def test_update_staticsite_users_with_resourcegroup_without_user_id_without_auth_provider(self):
        from azure.mgmt.web.models import StaticSiteUserARMResource

        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        authentication_provider = 'GitHub'
        user_id = '100'
        _mock_list_users_for_without_auth_provider(self, user_id, authentication_provider, user_details)

        update_staticsite_users(self.mock_cmd, self.name1, roles,
                                user_details=user_details, resource_group_name=self.rg1)

        self.staticapp_client.update_static_site_user.assert_called_once_with(self.rg1, self.name1,
            authentication_provider, user_id, static_site_user_envelope=StaticSiteUserARMResource(roles=roles))

    def test_update_staticsite_users_with_resourcegroup_without_user_id_without_auth_provider_user_not_found(self):
        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        _mock_list_users_for_without_auth_provider(self, 'dummy_user_id', 'dummy_authentication_provider',
                                                   'other_user_details')

        with self.assertRaises(CLIError):
            update_staticsite_users(self.mock_cmd, self.name1, roles,
                                    user_details=user_details, resource_group_name=self.rg1)

    def test_update_staticsite_users_with_resourcegroup_without_user_id(self):
        from azure.mgmt.web.models import StaticSiteUserARMResource

        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        authentication_provider = 'GitHub'
        user_id = '100'
        _mock_list_users_for_without_auth_provider(self, user_id, authentication_provider, user_details)

        update_staticsite_users(self.mock_cmd, self.name1, roles, authentication_provider=authentication_provider,
                                user_details=user_details, resource_group_name=self.rg1)

        self.staticapp_client.update_static_site_user.assert_called_once_with(self.rg1, self.name1,
            authentication_provider, user_id, static_site_user_envelope=StaticSiteUserARMResource(roles=roles))

    def test_update_staticsite_users_with_resourcegroup_without_user_id_user_not_found(self):
        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        authentication_provider = 'GitHub'
        _mock_list_users_for_without_auth_provider(self, 'dummy_user_id', 'dummy_authentication_provider',
                                                   'other_user_details')

        with self.assertRaises(CLIError):
            update_staticsite_users(self.mock_cmd, self.name1, roles, authentication_provider=authentication_provider,
                                    user_details=user_details, resource_group_name=self.rg1)

    def test_update_staticsite_users_with_resourcegroup_without_user_id_without_user_details(self):
        roles = 'Contributor,Reviewer'
        user_details = 'JohnDoe'
        authentication_provider = 'GitHub'
        user_id = '100'
        _mock_list_users_for_without_auth_provider(self, user_id, authentication_provider, user_details)

        with self.assertRaises(CLIError):
            update_staticsite_users(self.mock_cmd, self.name1, roles, authentication_provider=authentication_provider,
                                    resource_group_name=self.rg1)

    def test_list_staticsite_secrets(self):
        from azure.mgmt.web.models import StringDictionary
        self.staticapp_client.list_static_site_secrets.return_value = StringDictionary(properties={"apiKey": "key"})

        secret = list_staticsite_secrets(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.list_static_site_secrets.assert_called_once_with(resource_group_name=self.rg1, name=self.name1)
        from ast import literal_eval
        self.assertEqual(literal_eval(secret.__str__())["properties"]["apiKey"], "key")


    def test_staticsite_identity_assign(self):
        from azure.mgmt.web.models import ManagedServiceIdentity, ManagedServiceIdentityType
        self.mock_cmd.get_models.return_value = ManagedServiceIdentity, ManagedServiceIdentityType

        assign_identity(self.mock_cmd, self.rg1, self.name1)
        self.staticapp_client.begin_create_or_update_static_site.assert_called_once()

    def test_staticsite_identity_remove(self):
        from azure.mgmt.web.models import ManagedServiceIdentityType, Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties
        get_models = lambda s: ManagedServiceIdentityType if s == "ManagedServiceIdentityType" else Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties
        self.mock_cmd.get_models.side_effect = get_models

        remove_identity(self.mock_cmd, self.rg1, self.name1)
        self.staticapp_client.begin_create_or_update_static_site.assert_called_once()

    def test_staticsite_identity_show(self):
        mock_site = mock.MagicMock()
        mock_site.identity = "identity"
        self.staticapp_client.get_static_site.return_value = mock_site
        self.assertEqual(show_identity(self.mock_cmd, self.rg1, self.name1), "identity")


    def test_reset_staticsite_api_key(self):
        from azure.mgmt.web.models import StringDictionary, StaticSiteResetPropertiesARMResource
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.reset_static_site_api_key.return_value = StringDictionary(properties={"apiKey": "new_key"})
        self.mock_cmd.get_models.return_value = StaticSiteResetPropertiesARMResource

        secret = reset_staticsite_api_key(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_static_site.assert_called_once_with(self.rg1, self.name1)
        self.mock_cmd.get_models.assert_called_once_with('StaticSiteResetPropertiesARMResource')
        self.staticapp_client.reset_static_site_api_key.assert_called_once()

        from ast import literal_eval
        reset_envelope = literal_eval(self.staticapp_client.reset_static_site_api_key.call_args[1]["reset_properties_envelope"].__str__())
        self.assertEqual(reset_envelope["repository_token"], self.token1)

    @mock.patch("azure.cli.command_modules.appservice.static_sites.show_app")
    def test_functions_link(self, *args, **kwargs):
        functionapp_name = "functionapp"
        functionapp_resource_id = "/subscriptions/sub/resourceGroups/{}/providers/Microsoft.Web/sites/{}".format(
            self.rg1, functionapp_name
        )
        link_user_function(self.mock_cmd, self.name1, self.rg1, functionapp_resource_id)

        self.staticapp_client.begin_register_user_provided_function_app_with_static_site.assert_called_once()

    @mock.patch("azure.cli.command_modules.appservice.static_sites.get_user_function", return_value=[mock.MagicMock()])
    def test_functions_unlink(self, *args, **kwargs):
        unlink_user_function(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.detach_user_provided_function_app_from_static_site.assert_called_once()

    def test_functions_show(self, *args, **kwargs):
        get_user_function(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_user_provided_function_apps_for_static_site.assert_called_once()

    def test_enterprise_edge(self):
        self.staticapp_client.get_static_site.return_value = self.app1

        enable_staticwebapp_enterprise_edge(self.mock_cmd, self.name1, self.rg1, no_register=True)
        self.staticapp_client.update_static_site.assert_called_once()
        arg_list = self.staticapp_client.update_static_site.call_args[1]
        self.assertEqual(self.name1, arg_list["name"])
        self.assertEqual("enabled", arg_list["static_site_envelope"].enterprise_grade_cdn_status)

        disable_staticwebapp_enterprise_edge(self.mock_cmd, self.name1, self.rg1)
        self.assertEqual(self.staticapp_client.update_static_site.call_count, 2)
        arg_list = self.staticapp_client.update_static_site.call_args[1]
        self.assertEqual(self.name1, arg_list["name"])
        self.assertEqual("disabled", arg_list["static_site_envelope"].enterprise_grade_cdn_status)

        self.app1.enterprise_grade_cdn_status = "disabling"
        status = show_staticwebapp_enterprise_edge_status(self.mock_cmd, self.name1, self.rg1)
        self.assertEqual(status.get("enterpriseGradeCdnStatus"), "disabling")


def _set_up_client_mock(self):
    self.mock_cmd = mock.MagicMock()
    self.mock_cmd.cli_ctx = mock.MagicMock()
    self.staticapp_client = mock.MagicMock()

    client_factory_patcher = mock.patch(
        'azure.cli.command_modules.appservice.static_sites._get_staticsites_client_factory', autospec=True)
    self.addCleanup(client_factory_patcher.stop)
    self.mock_static_site_client_factory = client_factory_patcher.start()
    self.mock_static_site_client_factory.return_value = self.staticapp_client


def _set_up_fake_apps(self):
    from azure.mgmt.web.models import StaticSiteCustomDomainRequestPropertiesARMResource

    self.rg1 = 'rg1'
    self.name1 = 'name1'
    self.name1_not_exist = 'name1_not_exist'
    self.location1 = 'location1'
    self.source1 = 'https://github.com/Contoso/My-First-Static-App'
    self.branch1 = 'dev'
    self.token1 = 'TOKEN_1'
    self.environment1 = 'default'
    self.hostname1 = 'www.app1.com'
    self.hostname1_validation = StaticSiteCustomDomainRequestPropertiesARMResource(validation_method="cname-delegation")
    self.app1 = _contruct_static_site_object(
        self.rg1, self.name1, self.location1,
        self.source1, self.branch1, self.token1)

    self.rg2 = 'rg2'
    self.name2 = 'name2'
    self.location2 = 'location2'
    self.source2 = 'https://github.com/Contoso/My-Second-Static-App'
    self.branch2 = 'master'
    self.token2 = 'TOKEN_2'
    self.environment1 = 'prod'
    self.hostname1 = 'www.app2.com'
    self.app2 = _contruct_static_site_object(
        self.rg2, self.name2, self.location2,
        self.source2, self.branch2, self.token2)


def _contruct_static_site_object(rg, app_name, location, source, branch, token):
    from azure.mgmt.web.models import StaticSiteARMResource, SkuDescription
    app = StaticSiteARMResource(
        location=location,
        repository_url=source,
        branch=branch,
        repository_token=token,
        sku=SkuDescription(name='Free', tier='Free'))
    app.name = app_name
    app.id = \
        "/subscriptions/sub/resourceGroups/{}/providers/Microsoft.Web/staticSites/{}".format(rg, app_name)
    return app


def _mock_list_users_for_without_auth_provider(self, user_id, authentication_provider, user_details):
    class User:
        def __init__(self, name, provider, display_name):
            self.name = name
            self.provider = provider
            self.display_name = display_name

    user1 = User(user_id, authentication_provider, user_details)
    user2 = User(user_id + '2', authentication_provider + '2', user_details + '2')

    self.staticapp_client.list_static_site_users.return_value = [user1, user2]
