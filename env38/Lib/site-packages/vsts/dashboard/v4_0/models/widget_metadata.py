# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetMetadata(Model):
    """WidgetMetadata.

    :param allowed_sizes: Sizes supported by the Widget.
    :type allowed_sizes: list of :class:`WidgetSize <dashboard.v4_0.models.WidgetSize>`
    :param analytics_service_required: Opt-in boolean that indicates if the widget requires the Analytics Service to function. Widgets requiring the analytics service are hidden from the catalog if the Analytics Service is not available.
    :type analytics_service_required: bool
    :param catalog_icon_url: Resource for an icon in the widget catalog.
    :type catalog_icon_url: str
    :param catalog_info_url: Opt-in URL string pointing at widget information. Defaults to extension marketplace URL if omitted
    :type catalog_info_url: str
    :param configuration_contribution_id: The id of the underlying contribution defining the supplied Widget custom configuration UI. Null if custom configuration UI is not available.
    :type configuration_contribution_id: str
    :param configuration_contribution_relative_id: The relative id of the underlying contribution defining the supplied Widget custom configuration UI. Null if custom configuration UI is not available.
    :type configuration_contribution_relative_id: str
    :param configuration_required: Indicates if the widget requires configuration before being added to dashboard.
    :type configuration_required: bool
    :param content_uri: Uri for the WidgetFactory to get the widget
    :type content_uri: str
    :param contribution_id: The id of the underlying contribution defining the supplied Widget.
    :type contribution_id: str
    :param default_settings: Optional default settings to be copied into widget settings
    :type default_settings: str
    :param description: Summary information describing the widget.
    :type description: str
    :param is_enabled: Widgets can be disabled by the app store.  We'll need to gracefully handle for: - persistence (Allow) - Requests (Tag as disabled, and provide context)
    :type is_enabled: bool
    :param is_name_configurable: Opt-out boolean that indicates if the widget supports widget name/title configuration. Widgets ignoring the name should set it to false in the manifest.
    :type is_name_configurable: bool
    :param is_visible_from_catalog: Opt-out boolean indicating if the widget is hidden from the catalog.  For V1, only "pull" model widgets can be provided from the catalog.
    :type is_visible_from_catalog: bool
    :param lightbox_options: Opt-in lightbox properties
    :type lightbox_options: :class:`LightboxOptions <dashboard.v4_0.models.LightboxOptions>`
    :param loading_image_url: Resource for a loading placeholder image on dashboard
    :type loading_image_url: str
    :param name: User facing name of the widget type. Each widget must use a unique value here.
    :type name: str
    :param publisher_name: Publisher Name of this kind of widget.
    :type publisher_name: str
    :param supported_scopes: Data contract required for the widget to function and to work in its container.
    :type supported_scopes: list of WidgetScope
    :param targets: Contribution target IDs
    :type targets: list of str
    :param type_id: Dev-facing id of this kind of widget.
    :type type_id: str
    """

    _attribute_map = {
        'allowed_sizes': {'key': 'allowedSizes', 'type': '[WidgetSize]'},
        'analytics_service_required': {'key': 'analyticsServiceRequired', 'type': 'bool'},
        'catalog_icon_url': {'key': 'catalogIconUrl', 'type': 'str'},
        'catalog_info_url': {'key': 'catalogInfoUrl', 'type': 'str'},
        'configuration_contribution_id': {'key': 'configurationContributionId', 'type': 'str'},
        'configuration_contribution_relative_id': {'key': 'configurationContributionRelativeId', 'type': 'str'},
        'configuration_required': {'key': 'configurationRequired', 'type': 'bool'},
        'content_uri': {'key': 'contentUri', 'type': 'str'},
        'contribution_id': {'key': 'contributionId', 'type': 'str'},
        'default_settings': {'key': 'defaultSettings', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'is_name_configurable': {'key': 'isNameConfigurable', 'type': 'bool'},
        'is_visible_from_catalog': {'key': 'isVisibleFromCatalog', 'type': 'bool'},
        'lightbox_options': {'key': 'lightboxOptions', 'type': 'LightboxOptions'},
        'loading_image_url': {'key': 'loadingImageUrl', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'supported_scopes': {'key': 'supportedScopes', 'type': '[object]'},
        'targets': {'key': 'targets', 'type': '[str]'},
        'type_id': {'key': 'typeId', 'type': 'str'}
    }

    def __init__(self, allowed_sizes=None, analytics_service_required=None, catalog_icon_url=None, catalog_info_url=None, configuration_contribution_id=None, configuration_contribution_relative_id=None, configuration_required=None, content_uri=None, contribution_id=None, default_settings=None, description=None, is_enabled=None, is_name_configurable=None, is_visible_from_catalog=None, lightbox_options=None, loading_image_url=None, name=None, publisher_name=None, supported_scopes=None, targets=None, type_id=None):
        super(WidgetMetadata, self).__init__()
        self.allowed_sizes = allowed_sizes
        self.analytics_service_required = analytics_service_required
        self.catalog_icon_url = catalog_icon_url
        self.catalog_info_url = catalog_info_url
        self.configuration_contribution_id = configuration_contribution_id
        self.configuration_contribution_relative_id = configuration_contribution_relative_id
        self.configuration_required = configuration_required
        self.content_uri = content_uri
        self.contribution_id = contribution_id
        self.default_settings = default_settings
        self.description = description
        self.is_enabled = is_enabled
        self.is_name_configurable = is_name_configurable
        self.is_visible_from_catalog = is_visible_from_catalog
        self.lightbox_options = lightbox_options
        self.loading_image_url = loading_image_url
        self.name = name
        self.publisher_name = publisher_name
        self.supported_scopes = supported_scopes
        self.targets = targets
        self.type_id = type_id
