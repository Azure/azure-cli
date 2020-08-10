# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointType(Model):
    """ServiceEndpointType.

    :param authentication_schemes:
    :type authentication_schemes: list of :class:`ServiceEndpointAuthenticationScheme <task-agent.v4_0.models.ServiceEndpointAuthenticationScheme>`
    :param data_sources:
    :type data_sources: list of :class:`DataSource <task-agent.v4_0.models.DataSource>`
    :param dependency_data:
    :type dependency_data: list of :class:`DependencyData <task-agent.v4_0.models.DependencyData>`
    :param description:
    :type description: str
    :param display_name:
    :type display_name: str
    :param endpoint_url:
    :type endpoint_url: :class:`EndpointUrl <task-agent.v4_0.models.EndpointUrl>`
    :param help_link:
    :type help_link: :class:`HelpLink <task-agent.v4_0.models.HelpLink>`
    :param help_mark_down:
    :type help_mark_down: str
    :param icon_url:
    :type icon_url: str
    :param input_descriptors:
    :type input_descriptors: list of :class:`InputDescriptor <task-agent.v4_0.models.InputDescriptor>`
    :param name:
    :type name: str
    """

    _attribute_map = {
        'authentication_schemes': {'key': 'authenticationSchemes', 'type': '[ServiceEndpointAuthenticationScheme]'},
        'data_sources': {'key': 'dataSources', 'type': '[DataSource]'},
        'dependency_data': {'key': 'dependencyData', 'type': '[DependencyData]'},
        'description': {'key': 'description', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'endpoint_url': {'key': 'endpointUrl', 'type': 'EndpointUrl'},
        'help_link': {'key': 'helpLink', 'type': 'HelpLink'},
        'help_mark_down': {'key': 'helpMarkDown', 'type': 'str'},
        'icon_url': {'key': 'iconUrl', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, authentication_schemes=None, data_sources=None, dependency_data=None, description=None, display_name=None, endpoint_url=None, help_link=None, help_mark_down=None, icon_url=None, input_descriptors=None, name=None):
        super(ServiceEndpointType, self).__init__()
        self.authentication_schemes = authentication_schemes
        self.data_sources = data_sources
        self.dependency_data = dependency_data
        self.description = description
        self.display_name = display_name
        self.endpoint_url = endpoint_url
        self.help_link = help_link
        self.help_mark_down = help_mark_down
        self.icon_url = icon_url
        self.input_descriptors = input_descriptors
        self.name = name
