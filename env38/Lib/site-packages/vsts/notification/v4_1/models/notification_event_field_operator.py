# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventFieldOperator(Model):
    """NotificationEventFieldOperator.

    :param display_name: Gets or sets the display name of an operator
    :type display_name: str
    :param id: Gets or sets the id of an operator
    :type id: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, display_name=None, id=None):
        super(NotificationEventFieldOperator, self).__init__()
        self.display_name = display_name
        self.id = id
