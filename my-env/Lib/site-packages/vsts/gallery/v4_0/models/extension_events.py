# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionEvents(Model):
    """ExtensionEvents.

    :param events: Generic container for events data. The dictionary key denotes the type of event and the list contains properties related to that event
    :type events: dict
    :param extension_id: Id of the extension, this will never be sent back to the client. This field will mainly be used when EMS calls into Gallery REST API to update install/uninstall events for various extensions in one go.
    :type extension_id: str
    :param extension_name: Name of the extension
    :type extension_name: str
    :param publisher_name: Name of the publisher
    :type publisher_name: str
    """

    _attribute_map = {
        'events': {'key': 'events', 'type': '{[ExtensionEvent]}'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'}
    }

    def __init__(self, events=None, extension_id=None, extension_name=None, publisher_name=None):
        super(ExtensionEvents, self).__init__()
        self.events = events
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.publisher_name = publisher_name
