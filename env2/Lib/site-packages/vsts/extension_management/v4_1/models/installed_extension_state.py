# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InstalledExtensionState(Model):
    """InstalledExtensionState.

    :param flags: States of an installed extension
    :type flags: object
    :param installation_issues: List of installation issues
    :type installation_issues: list of :class:`InstalledExtensionStateIssue <extension-management.v4_1.models.InstalledExtensionStateIssue>`
    :param last_updated: The time at which this installation was last updated
    :type last_updated: datetime
    """

    _attribute_map = {
        'flags': {'key': 'flags', 'type': 'object'},
        'installation_issues': {'key': 'installationIssues', 'type': '[InstalledExtensionStateIssue]'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'}
    }

    def __init__(self, flags=None, installation_issues=None, last_updated=None):
        super(InstalledExtensionState, self).__init__()
        self.flags = flags
        self.installation_issues = installation_issues
        self.last_updated = last_updated
