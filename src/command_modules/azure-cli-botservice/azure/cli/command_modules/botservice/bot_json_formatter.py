# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._profile import Profile
from azure.cli.command_modules.botservice.web_app_operations import WebAppOperations


class BotJsonFormatter:  # pylint:disable=too-few-public-methods

    @staticmethod
    def create_bot_json(cmd, client, resource_group_name, resource_name, app_password=None, raw_bot_properties=None):
        """

        :param cmd:
        :param client:
        :param resource_group_name:
        :param resource_name:
        :param app_password:
        :param raw_bot_properties:
        :return: Dictionary

        """
        if not raw_bot_properties:
            raw_bot_properties = client.bots.get(
                resource_group_name=resource_group_name,
                resource_name=resource_name
            )

        if not app_password:
            site_name = WebAppOperations.get_bot_site_name(raw_bot_properties.properties.endpoint)
            app_settings = WebAppOperations.get_app_settings(
                cmd=cmd,
                resource_group_name=resource_group_name,
                name=site_name
            )
            app_password = [item['value'] for item in app_settings if item['name'] == 'MicrosoftAppPassword'][0]

        profile = Profile(cli_ctx=cmd.cli_ctx)
        return {
            'type': 'abs',
            'id': raw_bot_properties.name,
            'name': raw_bot_properties.properties.display_name,
            'appId': raw_bot_properties.properties.msa_app_id,
            'appPassword': app_password,
            'endpoint': raw_bot_properties.properties.endpoint,
            'resourceGroup': str(resource_group_name),
            'tenantId': profile.get_subscription(subscription=client.config.subscription_id)['tenantId'],
            'subscriptionId': client.config.subscription_id,
            'serviceName': resource_name
        }
