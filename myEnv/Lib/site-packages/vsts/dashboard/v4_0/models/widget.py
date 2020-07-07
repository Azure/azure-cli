# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Widget(Model):
    """Widget.

    :param _links:
    :type _links: :class:`ReferenceLinks <dashboard.v4_0.models.ReferenceLinks>`
    :param allowed_sizes: Refers to the allowed sizes for the widget. This gets populated when user wants to configure the widget
    :type allowed_sizes: list of :class:`WidgetSize <dashboard.v4_0.models.WidgetSize>`
    :param artifact_id: Refers to unique identifier of a feature artifact. Used for pinning+unpinning a specific artifact.
    :type artifact_id: str
    :param configuration_contribution_id:
    :type configuration_contribution_id: str
    :param configuration_contribution_relative_id:
    :type configuration_contribution_relative_id: str
    :param content_uri:
    :type content_uri: str
    :param contribution_id: The id of the underlying contribution defining the supplied Widget Configuration.
    :type contribution_id: str
    :param dashboard: Optional partial dashboard content, to support exchanging dashboard-level version ETag for widget-level APIs
    :type dashboard: :class:`Dashboard <dashboard.v4_0.models.Dashboard>`
    :param eTag:
    :type eTag: str
    :param id:
    :type id: str
    :param is_enabled:
    :type is_enabled: bool
    :param is_name_configurable:
    :type is_name_configurable: bool
    :param lightbox_options:
    :type lightbox_options: :class:`LightboxOptions <dashboard.v4_0.models.LightboxOptions>`
    :param loading_image_url:
    :type loading_image_url: str
    :param name:
    :type name: str
    :param position:
    :type position: :class:`WidgetPosition <dashboard.v4_0.models.WidgetPosition>`
    :param settings:
    :type settings: str
    :param settings_version:
    :type settings_version: :class:`SemanticVersion <dashboard.v4_0.models.SemanticVersion>`
    :param size:
    :type size: :class:`WidgetSize <dashboard.v4_0.models.WidgetSize>`
    :param type_id:
    :type type_id: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'allowed_sizes': {'key': 'allowedSizes', 'type': '[WidgetSize]'},
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'configuration_contribution_id': {'key': 'configurationContributionId', 'type': 'str'},
        'configuration_contribution_relative_id': {'key': 'configurationContributionRelativeId', 'type': 'str'},
        'content_uri': {'key': 'contentUri', 'type': 'str'},
        'contribution_id': {'key': 'contributionId', 'type': 'str'},
        'dashboard': {'key': 'dashboard', 'type': 'Dashboard'},
        'eTag': {'key': 'eTag', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'is_name_configurable': {'key': 'isNameConfigurable', 'type': 'bool'},
        'lightbox_options': {'key': 'lightboxOptions', 'type': 'LightboxOptions'},
        'loading_image_url': {'key': 'loadingImageUrl', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'position': {'key': 'position', 'type': 'WidgetPosition'},
        'settings': {'key': 'settings', 'type': 'str'},
        'settings_version': {'key': 'settingsVersion', 'type': 'SemanticVersion'},
        'size': {'key': 'size', 'type': 'WidgetSize'},
        'type_id': {'key': 'typeId', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, allowed_sizes=None, artifact_id=None, configuration_contribution_id=None, configuration_contribution_relative_id=None, content_uri=None, contribution_id=None, dashboard=None, eTag=None, id=None, is_enabled=None, is_name_configurable=None, lightbox_options=None, loading_image_url=None, name=None, position=None, settings=None, settings_version=None, size=None, type_id=None, url=None):
        super(Widget, self).__init__()
        self._links = _links
        self.allowed_sizes = allowed_sizes
        self.artifact_id = artifact_id
        self.configuration_contribution_id = configuration_contribution_id
        self.configuration_contribution_relative_id = configuration_contribution_relative_id
        self.content_uri = content_uri
        self.contribution_id = contribution_id
        self.dashboard = dashboard
        self.eTag = eTag
        self.id = id
        self.is_enabled = is_enabled
        self.is_name_configurable = is_name_configurable
        self.lightbox_options = lightbox_options
        self.loading_image_url = loading_image_url
        self.name = name
        self.position = position
        self.settings = settings
        self.settings_version = settings_version
        self.size = size
        self.type_id = type_id
        self.url = url
