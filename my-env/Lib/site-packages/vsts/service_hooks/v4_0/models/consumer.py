# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Consumer(Model):
    """Consumer.

    :param _links: Reference Links
    :type _links: :class:`ReferenceLinks <service-hooks.v4_0.models.ReferenceLinks>`
    :param actions: Gets this consumer's actions.
    :type actions: list of :class:`ConsumerAction <service-hooks.v4_0.models.ConsumerAction>`
    :param authentication_type: Gets or sets this consumer's authentication type.
    :type authentication_type: object
    :param description: Gets or sets this consumer's localized description.
    :type description: str
    :param external_configuration: Non-null only if subscriptions for this consumer are configured externally.
    :type external_configuration: :class:`ExternalConfigurationDescriptor <service-hooks.v4_0.models.ExternalConfigurationDescriptor>`
    :param id: Gets or sets this consumer's identifier.
    :type id: str
    :param image_url: Gets or sets this consumer's image URL, if any.
    :type image_url: str
    :param information_url: Gets or sets this consumer's information URL, if any.
    :type information_url: str
    :param input_descriptors: Gets or sets this consumer's input descriptors.
    :type input_descriptors: list of :class:`InputDescriptor <service-hooks.v4_0.models.InputDescriptor>`
    :param name: Gets or sets this consumer's localized name.
    :type name: str
    :param url: The url for this resource
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'actions': {'key': 'actions', 'type': '[ConsumerAction]'},
        'authentication_type': {'key': 'authenticationType', 'type': 'object'},
        'description': {'key': 'description', 'type': 'str'},
        'external_configuration': {'key': 'externalConfiguration', 'type': 'ExternalConfigurationDescriptor'},
        'id': {'key': 'id', 'type': 'str'},
        'image_url': {'key': 'imageUrl', 'type': 'str'},
        'information_url': {'key': 'informationUrl', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, actions=None, authentication_type=None, description=None, external_configuration=None, id=None, image_url=None, information_url=None, input_descriptors=None, name=None, url=None):
        super(Consumer, self).__init__()
        self._links = _links
        self.actions = actions
        self.authentication_type = authentication_type
        self.description = description
        self.external_configuration = external_configuration
        self.id = id
        self.image_url = image_url
        self.information_url = information_url
        self.input_descriptors = input_descriptors
        self.name = name
        self.url = url
