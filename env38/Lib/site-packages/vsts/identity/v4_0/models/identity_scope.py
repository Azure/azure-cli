# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentityScope(Model):
    """IdentityScope.

    :param administrators:
    :type administrators: :class:`str <identities.v4_0.models.str>`
    :param id:
    :type id: str
    :param is_active:
    :type is_active: bool
    :param is_global:
    :type is_global: bool
    :param local_scope_id:
    :type local_scope_id: str
    :param name:
    :type name: str
    :param parent_id:
    :type parent_id: str
    :param scope_type:
    :type scope_type: object
    :param securing_host_id:
    :type securing_host_id: str
    :param subject_descriptor:
    :type subject_descriptor: :class:`str <identities.v4_0.models.str>`
    """

    _attribute_map = {
        'administrators': {'key': 'administrators', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_active': {'key': 'isActive', 'type': 'bool'},
        'is_global': {'key': 'isGlobal', 'type': 'bool'},
        'local_scope_id': {'key': 'localScopeId', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'parent_id': {'key': 'parentId', 'type': 'str'},
        'scope_type': {'key': 'scopeType', 'type': 'object'},
        'securing_host_id': {'key': 'securingHostId', 'type': 'str'},
        'subject_descriptor': {'key': 'subjectDescriptor', 'type': 'str'}
    }

    def __init__(self, administrators=None, id=None, is_active=None, is_global=None, local_scope_id=None, name=None, parent_id=None, scope_type=None, securing_host_id=None, subject_descriptor=None):
        super(IdentityScope, self).__init__()
        self.administrators = administrators
        self.id = id
        self.is_active = is_active
        self.is_global = is_global
        self.local_scope_id = local_scope_id
        self.name = name
        self.parent_id = parent_id
        self.scope_type = scope_type
        self.securing_host_id = securing_host_id
        self.subject_descriptor = subject_descriptor
