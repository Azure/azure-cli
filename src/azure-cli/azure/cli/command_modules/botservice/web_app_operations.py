# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import HostType

try:
    # Try importing Python 3 urllib.parse
    from urllib.parse import urlsplit
except ImportError:
    # If urllib.parse was not imported, use Python 2 module urlparse
    from urlparse import urlsplit  # pylint: disable=import-error


class WebAppOperations:
    @staticmethod
    def get_bot_site_name(endpoint):
        split_parts = urlsplit(endpoint)
        return str(split_parts.netloc.split('.', 1)[0])

    @staticmethod
    def get_app_settings(cmd, resource_group_name, name, slot=None):
        result = WebAppOperations.__generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                           'list_application_settings', slot)

        client = WebAppOperations.__web_client_factory(cmd.cli_ctx)
        slot_app_setting_names = client.web_apps.list_slot_configuration_names(resource_group_name,
                                                                               name).app_setting_names
        return WebAppOperations.__build_app_settings_output(result.properties, slot_app_setting_names)

    @staticmethod
    def get_scm_url(cmd, resource_group_name, name, slot=None):
        webapp = WebAppOperations.__generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
        for host in webapp.host_name_ssl_states or []:
            if host.host_type == HostType.repository:
                return "https://{}".format(host.name)

        # this should not happen, but throw anyway
        raise ValueError('Failed to retrieve Scm Uri')

    @staticmethod
    def get_site_credential(cli_ctx, resource_group_name, name, slot=None):
        creds = WebAppOperations.__generic_site_operation(cli_ctx, resource_group_name, name,
                                                          'begin_list_publishing_credentials', slot)
        creds = creds.result()
        return creds.publishing_user_name, creds.publishing_password

    @staticmethod
    def __web_client_factory(cli_ctx, **_):
        return get_mgmt_service_client(cli_ctx, WebSiteManagementClient)

    @staticmethod
    def __build_app_settings_output(app_settings, slot_cfg_names):
        slot_cfg_names = slot_cfg_names or []
        return [{'name': p,
                 'value': app_settings[p],
                 'slotSetting': p in slot_cfg_names} for p in app_settings]

    @staticmethod
    def __generic_site_operation(cli_ctx, resource_group_name, name, operation_name, slot=None,
                                 extra_parameter=None, client=None):
        client = client or WebAppOperations.__web_client_factory(cli_ctx)
        operation = getattr(client.web_apps,
                            operation_name if slot is None else operation_name + '_slot')
        if slot is None:
            return (operation(resource_group_name, name)
                    if extra_parameter is None else operation(resource_group_name,  # pylint:disable=too-many-function-args
                                                              name, extra_parameter))

        return (operation(resource_group_name, name, slot)  # pylint:disable=too-many-function-args
                if extra_parameter is None else operation(resource_group_name, name, extra_parameter, slot))  # pylint:disable=too-many-function-args
