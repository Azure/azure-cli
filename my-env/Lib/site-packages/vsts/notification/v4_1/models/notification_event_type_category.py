# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventTypeCategory(Model):
    """NotificationEventTypeCategory.

    :param id: Gets or sets the unique identifier of this category.
    :type id: str
    :param name: Gets or sets the friendly name of this category.
    :type name: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, id=None, name=None):
        super(NotificationEventTypeCategory, self).__init__()
        self.id = id
        self.name = name
