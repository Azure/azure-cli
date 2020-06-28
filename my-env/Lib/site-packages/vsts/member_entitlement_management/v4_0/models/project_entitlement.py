# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectEntitlement(Model):
    """ProjectEntitlement.

    :param assignment_source:
    :type assignment_source: object
    :param group:
    :type group: :class:`Group <member-entitlement-management.v4_0.models.Group>`
    :param is_project_permission_inherited:
    :type is_project_permission_inherited: bool
    :param project_ref:
    :type project_ref: :class:`ProjectRef <member-entitlement-management.v4_0.models.ProjectRef>`
    :param team_refs:
    :type team_refs: list of :class:`TeamRef <member-entitlement-management.v4_0.models.TeamRef>`
    """

    _attribute_map = {
        'assignment_source': {'key': 'assignmentSource', 'type': 'object'},
        'group': {'key': 'group', 'type': 'Group'},
        'is_project_permission_inherited': {'key': 'isProjectPermissionInherited', 'type': 'bool'},
        'project_ref': {'key': 'projectRef', 'type': 'ProjectRef'},
        'team_refs': {'key': 'teamRefs', 'type': '[TeamRef]'}
    }

    def __init__(self, assignment_source=None, group=None, is_project_permission_inherited=None, project_ref=None, team_refs=None):
        super(ProjectEntitlement, self).__init__()
        self.assignment_source = assignment_source
        self.group = group
        self.is_project_permission_inherited = is_project_permission_inherited
        self.project_ref = project_ref
        self.team_refs = team_refs
