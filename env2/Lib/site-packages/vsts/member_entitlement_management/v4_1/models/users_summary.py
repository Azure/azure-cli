# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UsersSummary(Model):
    """UsersSummary.

    :param available_access_levels: Available Access Levels.
    :type available_access_levels: list of :class:`AccessLevel <member-entitlement-management.v4_1.models.AccessLevel>`
    :param extensions: Summary of Extensions in the account.
    :type extensions: list of :class:`ExtensionSummaryData <member-entitlement-management.v4_1.models.ExtensionSummaryData>`
    :param group_options: Group Options.
    :type group_options: list of :class:`GroupOption <member-entitlement-management.v4_1.models.GroupOption>`
    :param licenses: Summary of Licenses in the Account.
    :type licenses: list of :class:`LicenseSummaryData <member-entitlement-management.v4_1.models.LicenseSummaryData>`
    :param project_refs: Summary of Projects in the Account.
    :type project_refs: list of :class:`ProjectRef <member-entitlement-management.v4_1.models.ProjectRef>`
    """

    _attribute_map = {
        'available_access_levels': {'key': 'availableAccessLevels', 'type': '[AccessLevel]'},
        'extensions': {'key': 'extensions', 'type': '[ExtensionSummaryData]'},
        'group_options': {'key': 'groupOptions', 'type': '[GroupOption]'},
        'licenses': {'key': 'licenses', 'type': '[LicenseSummaryData]'},
        'project_refs': {'key': 'projectRefs', 'type': '[ProjectRef]'}
    }

    def __init__(self, available_access_levels=None, extensions=None, group_options=None, licenses=None, project_refs=None):
        super(UsersSummary, self).__init__()
        self.available_access_levels = available_access_levels
        self.extensions = extensions
        self.group_options = group_options
        self.licenses = licenses
        self.project_refs = project_refs
