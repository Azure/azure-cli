# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamMember(Model):
    """TeamMember.

    :param identity:
    :type identity: :class:`IdentityRef <microsoft.-visual-studio.-services.-web-api.v4_1.models.IdentityRef>`
    :param is_team_admin:
    :type is_team_admin: bool
    """

    _attribute_map = {
        'identity': {'key': 'identity', 'type': 'IdentityRef'},
        'is_team_admin': {'key': 'isTeamAdmin', 'type': 'bool'}
    }

    def __init__(self, identity=None, is_team_admin=None):
        super(TeamMember, self).__init__()
        self.identity = identity
        self.is_team_admin = is_team_admin
