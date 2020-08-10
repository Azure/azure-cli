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

    :param authentication_schemes: Authentication scheme of service endpoint type.
    :type authentication_schemes: list of :class:`ServiceEndpointAuthenticationScheme <task-agent.v4_1.models.ServiceEndpointAuthenticationScheme>`
    :param data_sources: Data sources of service endpoint type.
    :type data_sources: list of :class:`DataSource <task-agent.v4_1.models.DataSource>`
    :param dependency_data: Dependency data of service endpoint type.
    :type dependency_data: list of :class:`DependencyData <task-agent.v4_1.models.DependencyData>`
    :param description: Gets or sets the description of service endpoint type.
    :type description: str
    :param display_name: Gets or sets the display name of service endpoint type.
    :type display_name: str
    :param endpoint_url: Gets or sets the endpoint url of service endpoint type.
    :type endpoint_url: :class:`EndpointUrl <task-agent.v4_1.models.EndpointUrl>`
    :param help_link: Gets or sets the help link of service endpoint type.
    :type help_link: :class:`HelpLink <task-agent.v4_1.models.HelpLink>`
    :param help_mark_down:
    :type help_mark_down: str
    :param icon_url: Gets or sets the icon url of service endpoint type.
    :type icon_url: str
    :param input_descriptors: Input descriptor of service endpoint type.
    :type input_descriptors: list of :class:`InputDescriptor <task-agent.v4_1.models.InputDescriptor>`
    :param name: Gets or sets the name of service endpoint type.
    :type name: str
    :param trusted_hosts: Trusted hosts of a service endpoint type.
    :type trusted_hosts: list of str
    :param ui_contribution_id: Gets or sets the ui contribution id of service endpoint type.
    :type ui_contribution_id: str
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
        'name': {'key': 'name', 'type': 'str'},
        'trusted_hosts': {'key': 'trustedHosts', 'type': '[str]'},
        'ui_contribution_id': {'key': 'uiContributionId', 'type': 'str'}
    }

    def __init__(self, authentication_schemes=None, data_sources=None, dependency_data=None, description=None, display_name=None, endpoint_url=None, help_link=None, help_mark_down=None, icon_url=None, input_descriptors=None, name=None, trusted_hosts=None, ui_contribution_id=None):
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
        self.trusted_hosts = trusted_hosts
        self.ui_contribution_id = ui_contribution_id
