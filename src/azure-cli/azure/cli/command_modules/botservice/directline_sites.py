# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.botservice.models import (
    BotChannel,
    DirectLineChannel,
    DirectLineChannelProperties,
    DirectLineSite)


class DirectlineSites:
    """
    Helper class with static methods to manipulate Direct Line Sites
    associated with a Direct Line Channel Registration
    """
    @staticmethod
    def create(client, resource_group_name, resource_name, site_name, is_enabled=None,
               support_v3=None, enable_enhanced_auth=None, trusted_origins=None, show_secrets=None):
        bot = DirectlineSites._get_directline_instance(client, resource_group_name, resource_name, show_secrets)
        
        bot.properties.properties.sites.append(DirectLineSite(
            site_name=site_name,
            is_enabled=True,
            is_v1_enabled=True,
            is_v3_enabled=True,
        ))
        response = client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name='DirectLineChannel',
            properties=bot.properties
        )

        # If any parameter other than site_name is provided, a separate call to update the newly
        # created site is required.
        return_response = True
        for param in [is_enabled or support_v3 or enable_enhanced_auth or trusted_origins]:
            if param is not None:
                return_response = False
                break

        if return_response:
            return response

        bot = client.get(resource_group_name, resource_name, 'DirectLineChannel')
        for site in bot.properties.properties.sites:
            if site.site_name == site_name:
                site.is_enabled = site.is_enabled if is_enabled is None else is_enabled
                site.is_v3_enabled = site.is_v3_enabled if support_v3 is None else support_v3
                site.is_secure_site_enabled = site.is_secure_site_enabled if enable_enhanced_auth is None else enable_enhanced_auth
                site.trusted_origins=trusted_origins or site.trusted_origins
                break

        return client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name='DirectLineChannel',
            properties=bot.properties
        )

    @staticmethod
    def delete():
        return None

    @staticmethod
    def update():
        return None

    @staticmethod
    def list(client, resource_group_name, resource_name, show_secrets=None):
        channel = DirectlineSites._get_directline_instance(
            client,
            resource_group_name,
            resource_name,
            show_secrets)

        return channel.properties.sites

    @staticmethod
    def _get_directline_instance(client, resource_group_name, resource_name, show_secrets):
        if show_secrets:
            return client.list_with_keys(
                resource_group_name,
                resource_name,
                'DirectLineChannel',
            )
        return client.get(
            resource_group_name,
            resource_name,
            'DirectLineChannel',
        )
