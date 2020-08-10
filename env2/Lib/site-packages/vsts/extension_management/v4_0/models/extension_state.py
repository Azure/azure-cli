# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .installed_extension_state import InstalledExtensionState


class ExtensionState(InstalledExtensionState):
    """ExtensionState.

    :param flags: States of an installed extension
    :type flags: object
    :param installation_issues: List of installation issues
    :type installation_issues: list of :class:`InstalledExtensionStateIssue <extension-management.v4_0.models.InstalledExtensionStateIssue>`
    :param last_updated: The time at which this installation was last updated
    :type last_updated: datetime
    :param extension_name:
    :type extension_name: str
    :param last_version_check: The time at which the version was last checked
    :type last_version_check: datetime
    :param publisher_name:
    :type publisher_name: str
    :param version:
    :type version: str
    """

    _attribute_map = {
        'flags': {'key': 'flags', 'type': 'object'},
        'installation_issues': {'key': 'installationIssues', 'type': '[InstalledExtensionStateIssue]'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'last_version_check': {'key': 'lastVersionCheck', 'type': 'iso-8601'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, flags=None, installation_issues=None, last_updated=None, extension_name=None, last_version_check=None, publisher_name=None, version=None):
        super(ExtensionState, self).__init__(flags=flags, installation_issues=installation_issues, last_updated=last_updated)
        self.extension_name = extension_name
        self.last_version_check = last_version_check
        self.publisher_name = publisher_name
        self.version = version
