# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ApplicationType(Model):
    """ApplicationType.

    :param action_uri_link:
    :type action_uri_link: str
    :param aut_portal_link:
    :type aut_portal_link: str
    :param is_enabled:
    :type is_enabled: bool
    :param max_components_allowed_for_collection:
    :type max_components_allowed_for_collection: int
    :param max_counters_allowed:
    :type max_counters_allowed: int
    :param type:
    :type type: str
    """

    _attribute_map = {
        'action_uri_link': {'key': 'actionUriLink', 'type': 'str'},
        'aut_portal_link': {'key': 'autPortalLink', 'type': 'str'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'max_components_allowed_for_collection': {'key': 'maxComponentsAllowedForCollection', 'type': 'int'},
        'max_counters_allowed': {'key': 'maxCountersAllowed', 'type': 'int'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, action_uri_link=None, aut_portal_link=None, is_enabled=None, max_components_allowed_for_collection=None, max_counters_allowed=None, type=None):
        super(ApplicationType, self).__init__()
        self.action_uri_link = action_uri_link
        self.aut_portal_link = aut_portal_link
        self.is_enabled = is_enabled
        self.max_components_allowed_for_collection = max_components_allowed_for_collection
        self.max_counters_allowed = max_counters_allowed
        self.type = type
