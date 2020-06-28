# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EndpointUrl(Model):
    """EndpointUrl.

    :param depends_on: Gets or sets the dependency bindings.
    :type depends_on: :class:`DependsOn <service-endpoint.v4_1.models.DependsOn>`
    :param display_name: Gets or sets the display name of service endpoint url.
    :type display_name: str
    :param help_text: Gets or sets the help text of service endpoint url.
    :type help_text: str
    :param is_visible: Gets or sets the visibility of service endpoint url.
    :type is_visible: str
    :param value: Gets or sets the value of service endpoint url.
    :type value: str
    """

    _attribute_map = {
        'depends_on': {'key': 'dependsOn', 'type': 'DependsOn'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'help_text': {'key': 'helpText', 'type': 'str'},
        'is_visible': {'key': 'isVisible', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, depends_on=None, display_name=None, help_text=None, is_visible=None, value=None):
        super(EndpointUrl, self).__init__()
        self.depends_on = depends_on
        self.display_name = display_name
        self.help_text = help_text
        self.is_visible = is_visible
        self.value = value
