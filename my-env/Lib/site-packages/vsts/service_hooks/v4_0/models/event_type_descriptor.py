# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EventTypeDescriptor(Model):
    """EventTypeDescriptor.

    :param description: A localized description of the event type
    :type description: str
    :param id: A unique id for the event type
    :type id: str
    :param input_descriptors: Event-specific inputs
    :type input_descriptors: list of :class:`InputDescriptor <service-hooks.v4_0.models.InputDescriptor>`
    :param name: A localized friendly name for the event type
    :type name: str
    :param publisher_id: A unique id for the publisher of this event type
    :type publisher_id: str
    :param supported_resource_versions: Supported versions for the event's resource payloads.
    :type supported_resource_versions: list of str
    :param url: The url for this resource
    :type url: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'supported_resource_versions': {'key': 'supportedResourceVersions', 'type': '[str]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, input_descriptors=None, name=None, publisher_id=None, supported_resource_versions=None, url=None):
        super(EventTypeDescriptor, self).__init__()
        self.description = description
        self.id = id
        self.input_descriptors = input_descriptors
        self.name = name
        self.publisher_id = publisher_id
        self.supported_resource_versions = supported_resource_versions
        self.url = url
