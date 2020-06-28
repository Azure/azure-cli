# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Change(Model):
    """Change.

    :param change_type: The type of change that was made to the item.
    :type change_type: object
    :param item: Current version.
    :type item: object
    :param new_content: Content of the item after the change.
    :type new_content: :class:`ItemContent <git.v4_1.models.ItemContent>`
    :param source_server_item: Path of the item on the server.
    :type source_server_item: str
    :param url: URL to retrieve the item.
    :type url: str
    """

    _attribute_map = {
        'change_type': {'key': 'changeType', 'type': 'object'},
        'item': {'key': 'item', 'type': 'object'},
        'new_content': {'key': 'newContent', 'type': 'ItemContent'},
        'source_server_item': {'key': 'sourceServerItem', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, change_type=None, item=None, new_content=None, source_server_item=None, url=None):
        super(Change, self).__init__()
        self.change_type = change_type
        self.item = item
        self.new_content = new_content
        self.source_server_item = source_server_item
        self.url = url
