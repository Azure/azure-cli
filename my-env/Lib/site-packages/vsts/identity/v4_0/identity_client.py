# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class IdentityClient(VssClient):
    """Identity
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(IdentityClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '8a3d49b8-91f0-46ef-b33d-dda338c25db3'

    def create_or_bind_with_claims(self, source_identity):
        """CreateOrBindWithClaims.
        [Preview API]
        :param :class:`<Identity> <identity.v4_0.models.Identity>` source_identity:
        :rtype: :class:`<Identity> <identity.v4_0.models.Identity>`
        """
        content = self._serialize.body(source_identity, 'Identity')
        response = self._send(http_method='PUT',
                              location_id='90ddfe71-171c-446c-bf3b-b597cd562afd',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('Identity', response)

    def get_descriptor_by_id(self, id, is_master_id=None):
        """GetDescriptorById.
        [Preview API]
        :param str id:
        :param bool is_master_id:
        :rtype: :class:`<str> <identity.v4_0.models.str>`
        """
        route_values = {}
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        query_parameters = {}
        if is_master_id is not None:
            query_parameters['isMasterId'] = self._serialize.query('is_master_id', is_master_id, 'bool')
        response = self._send(http_method='GET',
                              location_id='a230389a-94f2-496c-839f-c929787496dd',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('str', response)

    def create_groups(self, container):
        """CreateGroups.
        :param :class:`<object> <identity.v4_0.models.object>` container:
        :rtype: [Identity]
        """
        content = self._serialize.body(container, 'object')
        response = self._send(http_method='POST',
                              location_id='5966283b-4196-4d57-9211-1b68f41ec1c2',
                              version='4.0',
                              content=content)
        return self._deserialize('[Identity]', self._unwrap_collection(response))

    def delete_group(self, group_id):
        """DeleteGroup.
        :param str group_id:
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        self._send(http_method='DELETE',
                   location_id='5966283b-4196-4d57-9211-1b68f41ec1c2',
                   version='4.0',
                   route_values=route_values)

    def list_groups(self, scope_ids=None, recurse=None, deleted=None, properties=None):
        """ListGroups.
        :param str scope_ids:
        :param bool recurse:
        :param bool deleted:
        :param str properties:
        :rtype: [Identity]
        """
        query_parameters = {}
        if scope_ids is not None:
            query_parameters['scopeIds'] = self._serialize.query('scope_ids', scope_ids, 'str')
        if recurse is not None:
            query_parameters['recurse'] = self._serialize.query('recurse', recurse, 'bool')
        if deleted is not None:
            query_parameters['deleted'] = self._serialize.query('deleted', deleted, 'bool')
        if properties is not None:
            query_parameters['properties'] = self._serialize.query('properties', properties, 'str')
        response = self._send(http_method='GET',
                              location_id='5966283b-4196-4d57-9211-1b68f41ec1c2',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[Identity]', self._unwrap_collection(response))

    def get_identity_changes(self, identity_sequence_id, group_sequence_id, scope_id=None):
        """GetIdentityChanges.
        :param int identity_sequence_id:
        :param int group_sequence_id:
        :param str scope_id:
        :rtype: :class:`<ChangedIdentities> <identity.v4_0.models.ChangedIdentities>`
        """
        query_parameters = {}
        if identity_sequence_id is not None:
            query_parameters['identitySequenceId'] = self._serialize.query('identity_sequence_id', identity_sequence_id, 'int')
        if group_sequence_id is not None:
            query_parameters['groupSequenceId'] = self._serialize.query('group_sequence_id', group_sequence_id, 'int')
        if scope_id is not None:
            query_parameters['scopeId'] = self._serialize.query('scope_id', scope_id, 'str')
        response = self._send(http_method='GET',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('ChangedIdentities', response)

    def get_user_identity_ids_by_domain_id(self, domain_id):
        """GetUserIdentityIdsByDomainId.
        :param str domain_id:
        :rtype: [str]
        """
        query_parameters = {}
        if domain_id is not None:
            query_parameters['domainId'] = self._serialize.query('domain_id', domain_id, 'str')
        response = self._send(http_method='GET',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def read_identities(self, descriptors=None, identity_ids=None, search_filter=None, filter_value=None, query_membership=None, properties=None, include_restricted_visibility=None, options=None):
        """ReadIdentities.
        :param str descriptors:
        :param str identity_ids:
        :param str search_filter:
        :param str filter_value:
        :param str query_membership:
        :param str properties:
        :param bool include_restricted_visibility:
        :param str options:
        :rtype: [Identity]
        """
        query_parameters = {}
        if descriptors is not None:
            query_parameters['descriptors'] = self._serialize.query('descriptors', descriptors, 'str')
        if identity_ids is not None:
            query_parameters['identityIds'] = self._serialize.query('identity_ids', identity_ids, 'str')
        if search_filter is not None:
            query_parameters['searchFilter'] = self._serialize.query('search_filter', search_filter, 'str')
        if filter_value is not None:
            query_parameters['filterValue'] = self._serialize.query('filter_value', filter_value, 'str')
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        if properties is not None:
            query_parameters['properties'] = self._serialize.query('properties', properties, 'str')
        if include_restricted_visibility is not None:
            query_parameters['includeRestrictedVisibility'] = self._serialize.query('include_restricted_visibility', include_restricted_visibility, 'bool')
        if options is not None:
            query_parameters['options'] = self._serialize.query('options', options, 'str')
        response = self._send(http_method='GET',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[Identity]', self._unwrap_collection(response))

    def read_identities_by_scope(self, scope_id, query_membership=None, properties=None):
        """ReadIdentitiesByScope.
        :param str scope_id:
        :param str query_membership:
        :param str properties:
        :rtype: [Identity]
        """
        query_parameters = {}
        if scope_id is not None:
            query_parameters['scopeId'] = self._serialize.query('scope_id', scope_id, 'str')
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        if properties is not None:
            query_parameters['properties'] = self._serialize.query('properties', properties, 'str')
        response = self._send(http_method='GET',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[Identity]', self._unwrap_collection(response))

    def read_identity(self, identity_id, query_membership=None, properties=None):
        """ReadIdentity.
        :param str identity_id:
        :param str query_membership:
        :param str properties:
        :rtype: :class:`<Identity> <identity.v4_0.models.Identity>`
        """
        route_values = {}
        if identity_id is not None:
            route_values['identityId'] = self._serialize.url('identity_id', identity_id, 'str')
        query_parameters = {}
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        if properties is not None:
            query_parameters['properties'] = self._serialize.query('properties', properties, 'str')
        response = self._send(http_method='GET',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('Identity', response)

    def update_identities(self, identities):
        """UpdateIdentities.
        :param :class:`<VssJsonCollectionWrapper> <identity.v4_0.models.VssJsonCollectionWrapper>` identities:
        :rtype: [IdentityUpdateData]
        """
        content = self._serialize.body(identities, 'VssJsonCollectionWrapper')
        response = self._send(http_method='PUT',
                              location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                              version='4.0',
                              content=content)
        return self._deserialize('[IdentityUpdateData]', self._unwrap_collection(response))

    def update_identity(self, identity, identity_id):
        """UpdateIdentity.
        :param :class:`<Identity> <identity.v4_0.models.Identity>` identity:
        :param str identity_id:
        """
        route_values = {}
        if identity_id is not None:
            route_values['identityId'] = self._serialize.url('identity_id', identity_id, 'str')
        content = self._serialize.body(identity, 'Identity')
        self._send(http_method='PUT',
                   location_id='28010c54-d0c0-4c89-a5b0-1c9e188b9fb7',
                   version='4.0',
                   route_values=route_values,
                   content=content)

    def create_identity(self, framework_identity_info):
        """CreateIdentity.
        :param :class:`<FrameworkIdentityInfo> <identity.v4_0.models.FrameworkIdentityInfo>` framework_identity_info:
        :rtype: :class:`<Identity> <identity.v4_0.models.Identity>`
        """
        content = self._serialize.body(framework_identity_info, 'FrameworkIdentityInfo')
        response = self._send(http_method='PUT',
                              location_id='dd55f0eb-6ea2-4fe4-9ebe-919e7dd1dfb4',
                              version='4.0',
                              content=content)
        return self._deserialize('Identity', response)

    def read_identity_batch(self, batch_info):
        """ReadIdentityBatch.
        [Preview API]
        :param :class:`<IdentityBatchInfo> <identity.v4_0.models.IdentityBatchInfo>` batch_info:
        :rtype: [Identity]
        """
        content = self._serialize.body(batch_info, 'IdentityBatchInfo')
        response = self._send(http_method='POST',
                              location_id='299e50df-fe45-4d3a-8b5b-a5836fac74dc',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('[Identity]', self._unwrap_collection(response))

    def get_identity_snapshot(self, scope_id):
        """GetIdentitySnapshot.
        [Preview API]
        :param str scope_id:
        :rtype: :class:`<IdentitySnapshot> <identity.v4_0.models.IdentitySnapshot>`
        """
        route_values = {}
        if scope_id is not None:
            route_values['scopeId'] = self._serialize.url('scope_id', scope_id, 'str')
        response = self._send(http_method='GET',
                              location_id='d56223df-8ccd-45c9-89b4-eddf692400d7',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('IdentitySnapshot', response)

    def get_max_sequence_id(self):
        """GetMaxSequenceId.
        Read the max sequence id of all the identities.
        :rtype: long
        """
        response = self._send(http_method='GET',
                              location_id='e4a70778-cb2c-4e85-b7cc-3f3c7ae2d408',
                              version='4.0')
        return self._deserialize('long', response)

    def get_self(self):
        """GetSelf.
        Read identity of the home tenant request user.
        :rtype: :class:`<IdentitySelf> <identity.v4_0.models.IdentitySelf>`
        """
        response = self._send(http_method='GET',
                              location_id='4bb02b5b-c120-4be2-b68e-21f7c50a4b82',
                              version='4.0')
        return self._deserialize('IdentitySelf', response)

    def add_member(self, container_id, member_id):
        """AddMember.
        [Preview API]
        :param str container_id:
        :param str member_id:
        :rtype: bool
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'str')
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        response = self._send(http_method='PUT',
                              location_id='8ba35978-138e-41f8-8963-7b1ea2c5f775',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('bool', response)

    def read_member(self, container_id, member_id, query_membership=None):
        """ReadMember.
        [Preview API]
        :param str container_id:
        :param str member_id:
        :param str query_membership:
        :rtype: :class:`<str> <identity.v4_0.models.str>`
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'str')
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        query_parameters = {}
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        response = self._send(http_method='GET',
                              location_id='8ba35978-138e-41f8-8963-7b1ea2c5f775',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('str', response)

    def read_members(self, container_id, query_membership=None):
        """ReadMembers.
        [Preview API]
        :param str container_id:
        :param str query_membership:
        :rtype: [str]
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'str')
        query_parameters = {}
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        response = self._send(http_method='GET',
                              location_id='8ba35978-138e-41f8-8963-7b1ea2c5f775',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def remove_member(self, container_id, member_id):
        """RemoveMember.
        [Preview API]
        :param str container_id:
        :param str member_id:
        :rtype: bool
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'str')
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        response = self._send(http_method='DELETE',
                              location_id='8ba35978-138e-41f8-8963-7b1ea2c5f775',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('bool', response)

    def read_member_of(self, member_id, container_id, query_membership=None):
        """ReadMemberOf.
        [Preview API]
        :param str member_id:
        :param str container_id:
        :param str query_membership:
        :rtype: :class:`<str> <identity.v4_0.models.str>`
        """
        route_values = {}
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'str')
        query_parameters = {}
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        response = self._send(http_method='GET',
                              location_id='22865b02-9e4a-479e-9e18-e35b8803b8a0',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('str', response)

    def read_members_of(self, member_id, query_membership=None):
        """ReadMembersOf.
        [Preview API]
        :param str member_id:
        :param str query_membership:
        :rtype: [str]
        """
        route_values = {}
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        query_parameters = {}
        if query_membership is not None:
            query_parameters['queryMembership'] = self._serialize.query('query_membership', query_membership, 'str')
        response = self._send(http_method='GET',
                              location_id='22865b02-9e4a-479e-9e18-e35b8803b8a0',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def create_scope(self, info, scope_id):
        """CreateScope.
        [Preview API]
        :param :class:`<CreateScopeInfo> <identity.v4_0.models.CreateScopeInfo>` info:
        :param str scope_id:
        :rtype: :class:`<IdentityScope> <identity.v4_0.models.IdentityScope>`
        """
        route_values = {}
        if scope_id is not None:
            route_values['scopeId'] = self._serialize.url('scope_id', scope_id, 'str')
        content = self._serialize.body(info, 'CreateScopeInfo')
        response = self._send(http_method='PUT',
                              location_id='4e11e2bf-1e79-4eb5-8f34-a6337bd0de38',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('IdentityScope', response)

    def delete_scope(self, scope_id):
        """DeleteScope.
        [Preview API]
        :param str scope_id:
        """
        route_values = {}
        if scope_id is not None:
            route_values['scopeId'] = self._serialize.url('scope_id', scope_id, 'str')
        self._send(http_method='DELETE',
                   location_id='4e11e2bf-1e79-4eb5-8f34-a6337bd0de38',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_scope_by_id(self, scope_id):
        """GetScopeById.
        [Preview API]
        :param str scope_id:
        :rtype: :class:`<IdentityScope> <identity.v4_0.models.IdentityScope>`
        """
        route_values = {}
        if scope_id is not None:
            route_values['scopeId'] = self._serialize.url('scope_id', scope_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4e11e2bf-1e79-4eb5-8f34-a6337bd0de38',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('IdentityScope', response)

    def get_scope_by_name(self, scope_name):
        """GetScopeByName.
        [Preview API]
        :param str scope_name:
        :rtype: :class:`<IdentityScope> <identity.v4_0.models.IdentityScope>`
        """
        query_parameters = {}
        if scope_name is not None:
            query_parameters['scopeName'] = self._serialize.query('scope_name', scope_name, 'str')
        response = self._send(http_method='GET',
                              location_id='4e11e2bf-1e79-4eb5-8f34-a6337bd0de38',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('IdentityScope', response)

    def rename_scope(self, rename_scope, scope_id):
        """RenameScope.
        [Preview API]
        :param :class:`<IdentityScope> <identity.v4_0.models.IdentityScope>` rename_scope:
        :param str scope_id:
        """
        route_values = {}
        if scope_id is not None:
            route_values['scopeId'] = self._serialize.url('scope_id', scope_id, 'str')
        content = self._serialize.body(rename_scope, 'IdentityScope')
        self._send(http_method='PATCH',
                   location_id='4e11e2bf-1e79-4eb5-8f34-a6337bd0de38',
                   version='4.0-preview.1',
                   route_values=route_values,
                   content=content)

    def get_signed_in_token(self):
        """GetSignedInToken.
        [Preview API]
        :rtype: :class:`<AccessTokenResult> <identity.v4_0.models.AccessTokenResult>`
        """
        response = self._send(http_method='GET',
                              location_id='6074ff18-aaad-4abb-a41e-5c75f6178057',
                              version='4.0-preview.1')
        return self._deserialize('AccessTokenResult', response)

    def get_signout_token(self):
        """GetSignoutToken.
        [Preview API]
        :rtype: :class:`<AccessTokenResult> <identity.v4_0.models.AccessTokenResult>`
        """
        response = self._send(http_method='GET',
                              location_id='be39e83c-7529-45e9-9c67-0410885880da',
                              version='4.0-preview.1')
        return self._deserialize('AccessTokenResult', response)

    def get_tenant(self, tenant_id):
        """GetTenant.
        [Preview API]
        :param str tenant_id:
        :rtype: :class:`<TenantInfo> <identity.v4_0.models.TenantInfo>`
        """
        route_values = {}
        if tenant_id is not None:
            route_values['tenantId'] = self._serialize.url('tenant_id', tenant_id, 'str')
        response = self._send(http_method='GET',
                              location_id='5f0a1723-2e2c-4c31-8cae-002d01bdd592',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('TenantInfo', response)

