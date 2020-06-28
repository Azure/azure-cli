# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ConsumerAction(Model):
    """ConsumerAction.

    :param _links: Reference Links
    :type _links: :class:`ReferenceLinks <service-hooks.v4_0.models.ReferenceLinks>`
    :param allow_resource_version_override: Gets or sets the flag indicating if resource version can be overridden when creating or editing a subscription.
    :type allow_resource_version_override: bool
    :param consumer_id: Gets or sets the identifier of the consumer to which this action belongs.
    :type consumer_id: str
    :param description: Gets or sets this action's localized description.
    :type description: str
    :param id: Gets or sets this action's identifier.
    :type id: str
    :param input_descriptors: Gets or sets this action's input descriptors.
    :type input_descriptors: list of :class:`InputDescriptor <service-hooks.v4_0.models.InputDescriptor>`
    :param name: Gets or sets this action's localized name.
    :type name: str
    :param supported_event_types: Gets or sets this action's supported event identifiers.
    :type supported_event_types: list of str
    :param supported_resource_versions: Gets or sets this action's supported resource versions.
    :type supported_resource_versions: dict
    :param url: The url for this resource
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'allow_resource_version_override': {'key': 'allowResourceVersionOverride', 'type': 'bool'},
        'consumer_id': {'key': 'consumerId', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'},
        'supported_event_types': {'key': 'supportedEventTypes', 'type': '[str]'},
        'supported_resource_versions': {'key': 'supportedResourceVersions', 'type': '{[str]}'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, allow_resource_version_override=None, consumer_id=None, description=None, id=None, input_descriptors=None, name=None, supported_event_types=None, supported_resource_versions=None, url=None):
        super(ConsumerAction, self).__init__()
        self._links = _links
        self.allow_resource_version_override = allow_resource_version_override
        self.consumer_id = consumer_id
        self.description = description
        self.id = id
        self.input_descriptors = input_descriptors
        self.name = name
        self.supported_event_types = supported_event_types
        self.supported_resource_versions = supported_resource_versions
        self.url = url
