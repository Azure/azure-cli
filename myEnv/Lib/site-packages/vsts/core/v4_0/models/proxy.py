# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Proxy(Model):
    """Proxy.

    :param authorization:
    :type authorization: :class:`ProxyAuthorization <core.v4_0.models.ProxyAuthorization>`
    :param description: This is a description string
    :type description: str
    :param friendly_name: The friendly name of the server
    :type friendly_name: str
    :param global_default:
    :type global_default: bool
    :param site: This is a string representation of the site that the proxy server is located in (e.g. "NA-WA-RED")
    :type site: str
    :param site_default:
    :type site_default: bool
    :param url: The URL of the proxy server
    :type url: str
    """

    _attribute_map = {
        'authorization': {'key': 'authorization', 'type': 'ProxyAuthorization'},
        'description': {'key': 'description', 'type': 'str'},
        'friendly_name': {'key': 'friendlyName', 'type': 'str'},
        'global_default': {'key': 'globalDefault', 'type': 'bool'},
        'site': {'key': 'site', 'type': 'str'},
        'site_default': {'key': 'siteDefault', 'type': 'bool'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, authorization=None, description=None, friendly_name=None, global_default=None, site=None, site_default=None, url=None):
        super(Proxy, self).__init__()
        self.authorization = authorization
        self.description = description
        self.friendly_name = friendly_name
        self.global_default = global_default
        self.site = site
        self.site_default = site_default
        self.url = url
