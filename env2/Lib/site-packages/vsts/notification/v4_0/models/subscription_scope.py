# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .event_scope import EventScope


class SubscriptionScope(EventScope):
    """SubscriptionScope.

    :param id: Required: This is the identity of the scope for the type.
    :type id: str
    :param type: Required: The event specific type of a scope.
    :type type: str
    :param name:
    :type name: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, id=None, type=None, name=None):
        super(SubscriptionScope, self).__init__(id=id, type=type)
        self.name = name
