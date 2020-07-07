# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CreateScopeInfo(Model):
    """CreateScopeInfo.

    :param admin_group_description:
    :type admin_group_description: str
    :param admin_group_name:
    :type admin_group_name: str
    :param creator_id:
    :type creator_id: str
    :param parent_scope_id:
    :type parent_scope_id: str
    :param scope_name:
    :type scope_name: str
    :param scope_type:
    :type scope_type: object
    """

    _attribute_map = {
        'admin_group_description': {'key': 'adminGroupDescription', 'type': 'str'},
        'admin_group_name': {'key': 'adminGroupName', 'type': 'str'},
        'creator_id': {'key': 'creatorId', 'type': 'str'},
        'parent_scope_id': {'key': 'parentScopeId', 'type': 'str'},
        'scope_name': {'key': 'scopeName', 'type': 'str'},
        'scope_type': {'key': 'scopeType', 'type': 'object'}
    }

    def __init__(self, admin_group_description=None, admin_group_name=None, creator_id=None, parent_scope_id=None, scope_name=None, scope_type=None):
        super(CreateScopeInfo, self).__init__()
        self.admin_group_description = admin_group_description
        self.admin_group_name = admin_group_name
        self.creator_id = creator_id
        self.parent_scope_id = parent_scope_id
        self.scope_name = scope_name
        self.scope_type = scope_type
