# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Identity(Model):
    """Identity.

    :param custom_display_name: The custom display name for the identity (if any). Setting this property to an empty string will clear the existing custom display name. Setting this property to null will not affect the existing persisted value (since null values do not get sent over the wire or to the database)
    :type custom_display_name: str
    :param descriptor:
    :type descriptor: :class:`str <identities.v4_0.models.str>`
    :param id:
    :type id: str
    :param is_active:
    :type is_active: bool
    :param is_container:
    :type is_container: bool
    :param master_id:
    :type master_id: str
    :param member_ids:
    :type member_ids: list of str
    :param member_of:
    :type member_of: list of :class:`str <identities.v4_0.models.str>`
    :param members:
    :type members: list of :class:`str <identities.v4_0.models.str>`
    :param meta_type_id:
    :type meta_type_id: int
    :param properties:
    :type properties: :class:`object <identities.v4_0.models.object>`
    :param provider_display_name: The display name for the identity as specified by the source identity provider.
    :type provider_display_name: str
    :param resource_version:
    :type resource_version: int
    :param subject_descriptor:
    :type subject_descriptor: :class:`str <identities.v4_0.models.str>`
    :param unique_user_id:
    :type unique_user_id: int
    """

    _attribute_map = {
        'custom_display_name': {'key': 'customDisplayName', 'type': 'str'},
        'descriptor': {'key': 'descriptor', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_active': {'key': 'isActive', 'type': 'bool'},
        'is_container': {'key': 'isContainer', 'type': 'bool'},
        'master_id': {'key': 'masterId', 'type': 'str'},
        'member_ids': {'key': 'memberIds', 'type': '[str]'},
        'member_of': {'key': 'memberOf', 'type': '[str]'},
        'members': {'key': 'members', 'type': '[str]'},
        'meta_type_id': {'key': 'metaTypeId', 'type': 'int'},
        'properties': {'key': 'properties', 'type': 'object'},
        'provider_display_name': {'key': 'providerDisplayName', 'type': 'str'},
        'resource_version': {'key': 'resourceVersion', 'type': 'int'},
        'subject_descriptor': {'key': 'subjectDescriptor', 'type': 'str'},
        'unique_user_id': {'key': 'uniqueUserId', 'type': 'int'}
    }

    def __init__(self, custom_display_name=None, descriptor=None, id=None, is_active=None, is_container=None, master_id=None, member_ids=None, member_of=None, members=None, meta_type_id=None, properties=None, provider_display_name=None, resource_version=None, subject_descriptor=None, unique_user_id=None):
        super(Identity, self).__init__()
        self.custom_display_name = custom_display_name
        self.descriptor = descriptor
        self.id = id
        self.is_active = is_active
        self.is_container = is_container
        self.master_id = master_id
        self.member_ids = member_ids
        self.member_of = member_of
        self.members = members
        self.meta_type_id = meta_type_id
        self.properties = properties
        self.provider_display_name = provider_display_name
        self.resource_version = resource_version
        self.subject_descriptor = subject_descriptor
        self.unique_user_id = unique_user_id
