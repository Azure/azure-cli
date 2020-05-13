# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.botservice.models import (DirectLineSite)
from knack.util import CLIError

DIRECT_LINE_CHANNEL = 'DirectLineChannel'

class DirectlineSites:
    """
    Helper class with static methods to manipulate Direct Line Sites
    associated with a Direct Line Channel Registration
    """
    @staticmethod
    def create(client, resource_group_name, resource_name, site_name, is_enabled=None,  # pylint: disable=too-many-arguments
               support_v3=None, enable_enhanced_auth=None, trusted_origins=None, show_secrets=None):
        channel = DirectlineSites._get_directline(client,
                                                  resource_group_name,
                                                  resource_name,
                                                  show_secrets)

        channel.properties.properties.sites.append(DirectLineSite(
            site_name=site_name,
            is_enabled=True,
            is_v1_enabled=True,
            is_v3_enabled=True,
        ))
        response = client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name=DIRECT_LINE_CHANNEL,
            properties=channel.properties
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

        channel = client.get(resource_group_name, resource_name, DIRECT_LINE_CHANNEL)
        for site in response.properties.properties.sites:
            if site.site_name == site_name:
                site.is_enabled = site.is_enabled if is_enabled is None else is_enabled
                site.is_v3_enabled = site.is_v3_enabled if support_v3 is None else support_v3
                site.is_secure_site_enabled = (site.is_secure_site_enabled if
                                               enable_enhanced_auth is None else
                                               enable_enhanced_auth)
                site.trusted_origins = trusted_origins or site.trusted_origins
                break

        return client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name=DIRECT_LINE_CHANNEL,
            properties=response.properties
        )

    @staticmethod
    def delete(client, resource_group_name, resource_name, site_name):
        channel = DirectlineSites._get_directline(client, resource_group_name, resource_name, False)
        saved_sites = [site for
                       site in
                       channel.properties.properties.sites if
                       site.site_name != site_name]
        channel.properties.properties.sites = saved_sites

        client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name=DIRECT_LINE_CHANNEL,
            properties=channel.properties
        )

    @staticmethod
    def update(client, resource_group_name, resource_name, site_name, is_enabled=None,  # pylint: disable=too-many-arguments
               support_v3=None, enable_enhanced_auth=None, trusted_origins=None, show_secrets=None):
        channel = DirectlineSites._get_directline(client,
                                                  resource_group_name,
                                                  resource_name,
                                                  show_secrets)
        site_updated = {'complete': False}
        def update_site(site):
            if site.site_name == site_name:
                site.is_enabled = site.is_enabled if is_enabled is None else is_enabled
                site.is_v3_enabled = site.is_v3_enabled if support_v3 is None else support_v3
                site.is_secure_site_enabled = (site.is_secure_site_enabled if
                                               enable_enhanced_auth is None else
                                               enable_enhanced_auth)
                site.trusted_origins = trusted_origins or site.trusted_origins
                site_updated['complete'] = True
            return site

        channel.properties.properties.sites = [update_site(site) for
                                               site in
                                               channel.properties.properties.sites]
        if not site_updated['complete']:
            raise CLIError("Direct Line site \"{}\" not found. First create Direct Line site via "\
                           "\"bot directline site create\"".format(site_name))
        return client.update(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            channel_name=DIRECT_LINE_CHANNEL,
            properties=channel.properties
        )

    @staticmethod
    def list(client, resource_group_name, resource_name, show_secrets=None):
        channel = DirectlineSites._get_directline(
            client,
            resource_group_name,
            resource_name,
            show_secrets)

        return channel.properties.sites

    @staticmethod
    def _get_directline(client, resource_group_name, resource_name, show_secrets):
        if show_secrets:
            return client.list_with_keys(
                resource_group_name,
                resource_name,
                DIRECT_LINE_CHANNEL,
            )
        return client.get(
            resource_group_name,
            resource_name,
            DIRECT_LINE_CHANNEL,
        )
