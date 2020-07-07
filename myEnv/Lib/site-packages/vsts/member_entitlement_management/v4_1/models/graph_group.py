# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .graph_member import GraphMember


class GraphGroup(GraphMember):
    """GraphGroup.

    :param _links: This field contains zero or more interesting links about the graph subject. These links may be invoked to obtain additional relationships or more detailed information about this graph subject.
    :type _links: :class:`ReferenceLinks <microsoft.-visual-studio.-services.-web-api.v4_1.models.ReferenceLinks>`
    :param descriptor: The descriptor is the primary way to reference the graph subject while the system is running. This field will uniquely identify the same graph subject across both Accounts and Organizations.
    :type descriptor: str
    :param display_name: This is the non-unique display name of the graph subject. To change this field, you must alter its value in the source provider.
    :type display_name: str
    :param url: This url is the full route to the source resource of this graph subject.
    :type url: str
    :param legacy_descriptor: [Internal Use Only] The legacy descriptor is here in case you need to access old version IMS using identity descriptor.
    :type legacy_descriptor: str
    :param origin: The type of source provider for the origin identifier (ex:AD, AAD, MSA)
    :type origin: str
    :param origin_id: The unique identifier from the system of origin. Typically a sid, object id or Guid. Linking and unlinking operations can cause this value to change for a user because the user is not backed by a different provider and has a different unique id in the new provider.
    :type origin_id: str
    :param subject_kind: This field identifies the type of the graph subject (ex: Group, Scope, User).
    :type subject_kind: str
    :param cuid: The Consistently Unique Identifier of the subject
    :type cuid: str
    :param domain: This represents the name of the container of origin for a graph member. (For MSA this is "Windows Live ID", for AD the name of the domain, for AAD the tenantID of the directory, for VSTS groups the ScopeId, etc)
    :type domain: str
    :param mail_address: The email address of record for a given graph member. This may be different than the principal name.
    :type mail_address: str
    :param principal_name: This is the PrincipalName of this graph member from the source provider. The source provider may change this field over time and it is not guaranteed to be immutable for the life of the graph member by VSTS.
    :type principal_name: str
    :param description: A short phrase to help human readers disambiguate groups with similar names
    :type description: str
    :param is_cross_project:
    :type is_cross_project: bool
    :param is_deleted:
    :type is_deleted: bool
    :param is_global_scope:
    :type is_global_scope: bool
    :param is_restricted_visible:
    :type is_restricted_visible: bool
    :param local_scope_id:
    :type local_scope_id: str
    :param scope_id:
    :type scope_id: str
    :param scope_name:
    :type scope_name: str
    :param scope_type:
    :type scope_type: str
    :param securing_host_id:
    :type securing_host_id: str
    :param special_type:
    :type special_type: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'descriptor': {'key': 'descriptor', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'legacy_descriptor': {'key': 'legacyDescriptor', 'type': 'str'},
        'origin': {'key': 'origin', 'type': 'str'},
        'origin_id': {'key': 'originId', 'type': 'str'},
        'subject_kind': {'key': 'subjectKind', 'type': 'str'},
        'cuid': {'key': 'cuid', 'type': 'str'},
        'domain': {'key': 'domain', 'type': 'str'},
        'mail_address': {'key': 'mailAddress', 'type': 'str'},
        'principal_name': {'key': 'principalName', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'is_cross_project': {'key': 'isCrossProject', 'type': 'bool'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'is_global_scope': {'key': 'isGlobalScope', 'type': 'bool'},
        'is_restricted_visible': {'key': 'isRestrictedVisible', 'type': 'bool'},
        'local_scope_id': {'key': 'localScopeId', 'type': 'str'},
        'scope_id': {'key': 'scopeId', 'type': 'str'},
        'scope_name': {'key': 'scopeName', 'type': 'str'},
        'scope_type': {'key': 'scopeType', 'type': 'str'},
        'securing_host_id': {'key': 'securingHostId', 'type': 'str'},
        'special_type': {'key': 'specialType', 'type': 'str'}
    }

    def __init__(self, _links=None, descriptor=None, display_name=None, url=None, legacy_descriptor=None, origin=None, origin_id=None, subject_kind=None, cuid=None, domain=None, mail_address=None, principal_name=None, description=None, is_cross_project=None, is_deleted=None, is_global_scope=None, is_restricted_visible=None, local_scope_id=None, scope_id=None, scope_name=None, scope_type=None, securing_host_id=None, special_type=None):
        super(GraphGroup, self).__init__(_links=_links, descriptor=descriptor, display_name=display_name, url=url, legacy_descriptor=legacy_descriptor, origin=origin, origin_id=origin_id, subject_kind=subject_kind, cuid=cuid, domain=domain, mail_address=mail_address, principal_name=principal_name)
        self.description = description
        self.is_cross_project = is_cross_project
        self.is_deleted = is_deleted
        self.is_global_scope = is_global_scope
        self.is_restricted_visible = is_restricted_visible
        self.local_scope_id = local_scope_id
        self.scope_id = scope_id
        self.scope_name = scope_name
        self.scope_type = scope_type
        self.securing_host_id = securing_host_id
        self.special_type = special_type
