# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphScopeCreationContext(Model):
    """GraphScopeCreationContext.

    :param admin_group_description: Set this field to override the default description of this scope's admin group.
    :type admin_group_description: str
    :param admin_group_name: All scopes have an Administrator Group that controls access to the contents of the scope. Set this field to use a non-default group name for that administrators group.
    :type admin_group_name: str
    :param creator_id: Set this optional field if this scope is created on behalf of a user other than the user making the request. This should be the Id of the user that is not the requester.
    :type creator_id: str
    :param name: The scope must be provided with a unique name within the parent scope. This means the created scope can have a parent or child with the same name, but no siblings with the same name.
    :type name: str
    :param scope_type: The type of scope being created.
    :type scope_type: object
    :param storage_key: An optional ID that uniquely represents the scope within it's parent scope. If this parameter is not provided, Vsts will generate on automatically.
    :type storage_key: str
    """

    _attribute_map = {
        'admin_group_description': {'key': 'adminGroupDescription', 'type': 'str'},
        'admin_group_name': {'key': 'adminGroupName', 'type': 'str'},
        'creator_id': {'key': 'creatorId', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'scope_type': {'key': 'scopeType', 'type': 'object'},
        'storage_key': {'key': 'storageKey', 'type': 'str'}
    }

    def __init__(self, admin_group_description=None, admin_group_name=None, creator_id=None, name=None, scope_type=None, storage_key=None):
        super(GraphScopeCreationContext, self).__init__()
        self.admin_group_description = admin_group_description
        self.admin_group_name = admin_group_name
        self.creator_id = creator_id
        self.name = name
        self.scope_type = scope_type
        self.storage_key = storage_key
