# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .extension_manifest import ExtensionManifest


class InstalledExtension(ExtensionManifest):
    """InstalledExtension.

    :param base_uri: Uri used as base for other relative uri's defined in extension
    :type base_uri: str
    :param contributions: List of contributions made by this extension
    :type contributions: list of :class:`Contribution <extension-management.v4_0.models.Contribution>`
    :param contribution_types: List of contribution types defined by this extension
    :type contribution_types: list of :class:`ContributionType <extension-management.v4_0.models.ContributionType>`
    :param demands: List of explicit demands required by this extension
    :type demands: list of str
    :param event_callbacks: Collection of endpoints that get called when particular extension events occur
    :type event_callbacks: :class:`ExtensionEventCallbackCollection <extension-management.v4_0.models.ExtensionEventCallbackCollection>`
    :param fallback_base_uri: Secondary location that can be used as base for other relative uri's defined in extension
    :type fallback_base_uri: str
    :param language: Language Culture Name set by the Gallery
    :type language: str
    :param licensing: How this extension behaves with respect to licensing
    :type licensing: :class:`ExtensionLicensing <extension-management.v4_0.models.ExtensionLicensing>`
    :param manifest_version: Version of the extension manifest format/content
    :type manifest_version: float
    :param scopes: List of all oauth scopes required by this extension
    :type scopes: list of str
    :param service_instance_type: The ServiceInstanceType(Guid) of the VSTS service that must be available to an account in order for the extension to be installed
    :type service_instance_type: str
    :param extension_id: The friendly extension id for this extension - unique for a given publisher.
    :type extension_id: str
    :param extension_name: The display name of the extension.
    :type extension_name: str
    :param files: This is the set of files available from the extension.
    :type files: list of :class:`ExtensionFile <extension-management.v4_0.models.ExtensionFile>`
    :param flags: Extension flags relevant to contribution consumers
    :type flags: object
    :param install_state: Information about this particular installation of the extension
    :type install_state: :class:`InstalledExtensionState <extension-management.v4_0.models.InstalledExtensionState>`
    :param last_published: This represents the date/time the extensions was last updated in the gallery. This doesnt mean this version was updated the value represents changes to any and all versions of the extension.
    :type last_published: datetime
    :param publisher_id: Unique id of the publisher of this extension
    :type publisher_id: str
    :param publisher_name: The display name of the publisher
    :type publisher_name: str
    :param registration_id: Unique id for this extension (the same id is used for all versions of a single extension)
    :type registration_id: str
    :param version: Version of this extension
    :type version: str
    """

    _attribute_map = {
        'base_uri': {'key': 'baseUri', 'type': 'str'},
        'contributions': {'key': 'contributions', 'type': '[Contribution]'},
        'contribution_types': {'key': 'contributionTypes', 'type': '[ContributionType]'},
        'demands': {'key': 'demands', 'type': '[str]'},
        'event_callbacks': {'key': 'eventCallbacks', 'type': 'ExtensionEventCallbackCollection'},
        'fallback_base_uri': {'key': 'fallbackBaseUri', 'type': 'str'},
        'language': {'key': 'language', 'type': 'str'},
        'licensing': {'key': 'licensing', 'type': 'ExtensionLicensing'},
        'manifest_version': {'key': 'manifestVersion', 'type': 'float'},
        'scopes': {'key': 'scopes', 'type': '[str]'},
        'service_instance_type': {'key': 'serviceInstanceType', 'type': 'str'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'files': {'key': 'files', 'type': '[ExtensionFile]'},
        'flags': {'key': 'flags', 'type': 'object'},
        'install_state': {'key': 'installState', 'type': 'InstalledExtensionState'},
        'last_published': {'key': 'lastPublished', 'type': 'iso-8601'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'registration_id': {'key': 'registrationId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, base_uri=None, contributions=None, contribution_types=None, demands=None, event_callbacks=None, fallback_base_uri=None, language=None, licensing=None, manifest_version=None, scopes=None, service_instance_type=None, extension_id=None, extension_name=None, files=None, flags=None, install_state=None, last_published=None, publisher_id=None, publisher_name=None, registration_id=None, version=None):
        super(InstalledExtension, self).__init__(base_uri=base_uri, contributions=contributions, contribution_types=contribution_types, demands=demands, event_callbacks=event_callbacks, fallback_base_uri=fallback_base_uri, language=language, licensing=licensing, manifest_version=manifest_version, scopes=scopes, service_instance_type=service_instance_type)
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.files = files
        self.flags = flags
        self.install_state = install_state
        self.last_published = last_published
        self.publisher_id = publisher_id
        self.publisher_name = publisher_name
        self.registration_id = registration_id
        self.version = version
