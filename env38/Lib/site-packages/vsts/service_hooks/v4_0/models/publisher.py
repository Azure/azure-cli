# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Publisher(Model):
    """Publisher.

    :param _links: Reference Links
    :type _links: :class:`ReferenceLinks <service-hooks.v4_0.models.ReferenceLinks>`
    :param description: Gets this publisher's localized description.
    :type description: str
    :param id: Gets this publisher's identifier.
    :type id: str
    :param input_descriptors: Publisher-specific inputs
    :type input_descriptors: list of :class:`InputDescriptor <service-hooks.v4_0.models.InputDescriptor>`
    :param name: Gets this publisher's localized name.
    :type name: str
    :param service_instance_type: The service instance type of the first party publisher.
    :type service_instance_type: str
    :param supported_events: Gets this publisher's supported event types.
    :type supported_events: list of :class:`EventTypeDescriptor <service-hooks.v4_0.models.EventTypeDescriptor>`
    :param url: The url for this resource
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'},
        'service_instance_type': {'key': 'serviceInstanceType', 'type': 'str'},
        'supported_events': {'key': 'supportedEvents', 'type': '[EventTypeDescriptor]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, description=None, id=None, input_descriptors=None, name=None, service_instance_type=None, supported_events=None, url=None):
        super(Publisher, self).__init__()
        self._links = _links
        self.description = description
        self.id = id
        self.input_descriptors = input_descriptors
        self.name = name
        self.service_instance_type = service_instance_type
        self.supported_events = supported_events
        self.url = url
