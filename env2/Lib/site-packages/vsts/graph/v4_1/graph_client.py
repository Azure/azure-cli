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


class GraphClient(VssClient):
    """Graph
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(GraphClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'bb1e7ec9-e901-4b68-999a-de7012b920f8'

    def get_descriptor(self, storage_key):
        """GetDescriptor.
        [Preview API] Resolve a storage key to a descriptor
        :param str storage_key: Storage key of the subject (user, group, scope, etc.) to resolve
        :rtype: :class:`<GraphDescriptorResult> <graph.v4_1.models.GraphDescriptorResult>`
        """
        route_values = {}
        if storage_key is not None:
            route_values['storageKey'] = self._serialize.url('storage_key', storage_key, 'str')
        response = self._send(http_method='GET',
                              location_id='048aee0a-7072-4cde-ab73-7af77b1e0b4e',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphDescriptorResult', response)

    def create_group(self, creation_context, scope_descriptor=None, group_descriptors=None):
        """CreateGroup.
        [Preview API] Create a new VSTS group or materialize an existing AAD group.
        :param :class:`<GraphGroupCreationContext> <graph.v4_1.models.GraphGroupCreationContext>` creation_context: The subset of the full graph group used to uniquely find the graph subject in an external provider.
        :param str scope_descriptor: A descriptor referencing the scope (collection, project) in which the group should be created. If omitted, will be created in the scope of the enclosing account or organization. Valid only for VSTS groups.
        :param [str] group_descriptors: A comma separated list of descriptors referencing groups you want the graph group to join
        :rtype: :class:`<GraphGroup> <graph.v4_1.models.GraphGroup>`
        """
        query_parameters = {}
        if scope_descriptor is not None:
            query_parameters['scopeDescriptor'] = self._serialize.query('scope_descriptor', scope_descriptor, 'str')
        if group_descriptors is not None:
            group_descriptors = ",".join(group_descriptors)
            query_parameters['groupDescriptors'] = self._serialize.query('group_descriptors', group_descriptors, 'str')
        content = self._serialize.body(creation_context, 'GraphGroupCreationContext')
        response = self._send(http_method='POST',
                              location_id='ebbe6af8-0b91-4c13-8cf1-777c14858188',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GraphGroup', response)

    def delete_group(self, group_descriptor):
        """DeleteGroup.
        [Preview API] Removes a VSTS group from all of its parent groups.
        :param str group_descriptor: The descriptor of the group to delete.
        """
        route_values = {}
        if group_descriptor is not None:
            route_values['groupDescriptor'] = self._serialize.url('group_descriptor', group_descriptor, 'str')
        self._send(http_method='DELETE',
                   location_id='ebbe6af8-0b91-4c13-8cf1-777c14858188',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_group(self, group_descriptor):
        """GetGroup.
        [Preview API] Get a group by its descriptor.
        :param str group_descriptor: The descriptor of the desired graph group.
        :rtype: :class:`<GraphGroup> <graph.v4_1.models.GraphGroup>`
        """
        route_values = {}
        if group_descriptor is not None:
            route_values['groupDescriptor'] = self._serialize.url('group_descriptor', group_descriptor, 'str')
        response = self._send(http_method='GET',
                              location_id='ebbe6af8-0b91-4c13-8cf1-777c14858188',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphGroup', response)

    def list_groups(self, scope_descriptor=None, subject_types=None, continuation_token=None):
        """ListGroups.
        [Preview API] Gets a list of all groups in the current scope (usually organization or account).
        :param str scope_descriptor: Specify a non-default scope (collection, project) to search for groups.
        :param [str] subject_types: A comma separated list of user subject subtypes to reduce the retrieved results, e.g. Microsoft.IdentityModel.Claims.ClaimsIdentity
        :param str continuation_token: An opaque data blob that allows the next page of data to resume immediately after where the previous page ended. The only reliable way to know if there is more data left is the presence of a continuation token.
        :rtype: :class:`<PagedGraphGroups> <graph.v4_1.models.PagedGraphGroups>`
        """
        query_parameters = {}
        if scope_descriptor is not None:
            query_parameters['scopeDescriptor'] = self._serialize.query('scope_descriptor', scope_descriptor, 'str')
        if subject_types is not None:
            subject_types = ",".join(subject_types)
            query_parameters['subjectTypes'] = self._serialize.query('subject_types', subject_types, 'str')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'str')
        response = self._send(http_method='GET',
                              location_id='ebbe6af8-0b91-4c13-8cf1-777c14858188',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        response_object = models.PagedGraphGroups()
        response_object.graph_groups = self._deserialize('[GraphGroup]', self._unwrap_collection(response))
        response_object.continuation_token = response.headers.get('X-MS-ContinuationToken')
        return response_object

    def update_group(self, group_descriptor, patch_document):
        """UpdateGroup.
        [Preview API] Update the properties of a VSTS group.
        :param str group_descriptor: The descriptor of the group to modify.
        :param :class:`<[JsonPatchOperation]> <graph.v4_1.models.[JsonPatchOperation]>` patch_document: The JSON+Patch document containing the fields to alter.
        :rtype: :class:`<GraphGroup> <graph.v4_1.models.GraphGroup>`
        """
        route_values = {}
        if group_descriptor is not None:
            route_values['groupDescriptor'] = self._serialize.url('group_descriptor', group_descriptor, 'str')
        content = self._serialize.body(patch_document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='ebbe6af8-0b91-4c13-8cf1-777c14858188',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('GraphGroup', response)

    def add_membership(self, subject_descriptor, container_descriptor):
        """AddMembership.
        [Preview API] Create a new membership between a container and subject.
        :param str subject_descriptor: A descriptor to a group or user that can be the child subject in the relationship.
        :param str container_descriptor: A descriptor to a group that can be the container in the relationship.
        :rtype: :class:`<GraphMembership> <graph.v4_1.models.GraphMembership>`
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        if container_descriptor is not None:
            route_values['containerDescriptor'] = self._serialize.url('container_descriptor', container_descriptor, 'str')
        response = self._send(http_method='PUT',
                              location_id='3fd2e6ca-fb30-443a-b579-95b19ed0934c',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphMembership', response)

    def check_membership_existence(self, subject_descriptor, container_descriptor):
        """CheckMembershipExistence.
        [Preview API] Check to see if a membership relationship between a container and subject exists.
        :param str subject_descriptor: The group or user that is a child subject of the relationship.
        :param str container_descriptor: The group that is the container in the relationship.
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        if container_descriptor is not None:
            route_values['containerDescriptor'] = self._serialize.url('container_descriptor', container_descriptor, 'str')
        self._send(http_method='HEAD',
                   location_id='3fd2e6ca-fb30-443a-b579-95b19ed0934c',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_membership(self, subject_descriptor, container_descriptor):
        """GetMembership.
        [Preview API] Get a membership relationship between a container and subject.
        :param str subject_descriptor: A descriptor to the child subject in the relationship.
        :param str container_descriptor: A descriptor to the container in the relationship.
        :rtype: :class:`<GraphMembership> <graph.v4_1.models.GraphMembership>`
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        if container_descriptor is not None:
            route_values['containerDescriptor'] = self._serialize.url('container_descriptor', container_descriptor, 'str')
        response = self._send(http_method='GET',
                              location_id='3fd2e6ca-fb30-443a-b579-95b19ed0934c',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphMembership', response)

    def remove_membership(self, subject_descriptor, container_descriptor):
        """RemoveMembership.
        [Preview API] Deletes a membership between a container and subject.
        :param str subject_descriptor: A descriptor to a group or user that is the child subject in the relationship.
        :param str container_descriptor: A descriptor to a group that is the container in the relationship.
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        if container_descriptor is not None:
            route_values['containerDescriptor'] = self._serialize.url('container_descriptor', container_descriptor, 'str')
        self._send(http_method='DELETE',
                   location_id='3fd2e6ca-fb30-443a-b579-95b19ed0934c',
                   version='4.1-preview.1',
                   route_values=route_values)

    def list_memberships(self, subject_descriptor, direction=None, depth=None):
        """ListMemberships.
        [Preview API] Get all the memberships where this descriptor is a member in the relationship.
        :param str subject_descriptor: Fetch all direct memberships of this descriptor.
        :param str direction: Defaults to Up.
        :param int depth: The maximum number of edges to traverse up or down the membership tree. Currently the only supported value is '1'.
        :rtype: [GraphMembership]
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        query_parameters = {}
        if direction is not None:
            query_parameters['direction'] = self._serialize.query('direction', direction, 'str')
        if depth is not None:
            query_parameters['depth'] = self._serialize.query('depth', depth, 'int')
        response = self._send(http_method='GET',
                              location_id='e34b6394-6b30-4435-94a9-409a5eef3e31',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GraphMembership]', self._unwrap_collection(response))

    def get_membership_state(self, subject_descriptor):
        """GetMembershipState.
        [Preview API] Check whether a subject is active or inactive.
        :param str subject_descriptor: Descriptor of the subject (user, group, scope, etc.) to check state of
        :rtype: :class:`<GraphMembershipState> <graph.v4_1.models.GraphMembershipState>`
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        response = self._send(http_method='GET',
                              location_id='1ffe5c94-1144-4191-907b-d0211cad36a8',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphMembershipState', response)

    def get_storage_key(self, subject_descriptor):
        """GetStorageKey.
        [Preview API] Resolve a descriptor to a storage key.
        :param str subject_descriptor:
        :rtype: :class:`<GraphStorageKeyResult> <graph.v4_1.models.GraphStorageKeyResult>`
        """
        route_values = {}
        if subject_descriptor is not None:
            route_values['subjectDescriptor'] = self._serialize.url('subject_descriptor', subject_descriptor, 'str')
        response = self._send(http_method='GET',
                              location_id='eb85f8cc-f0f6-4264-a5b1-ffe2e4d4801f',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphStorageKeyResult', response)

    def lookup_subjects(self, subject_lookup):
        """LookupSubjects.
        [Preview API] Resolve descriptors to users, groups or scopes (Subjects) in a batch.
        :param :class:`<GraphSubjectLookup> <graph.v4_1.models.GraphSubjectLookup>` subject_lookup: A list of descriptors that specifies a subset of subjects to retrieve. Each descriptor uniquely identifies the subject across all instance scopes, but only at a single point in time.
        :rtype: {GraphSubject}
        """
        content = self._serialize.body(subject_lookup, 'GraphSubjectLookup')
        response = self._send(http_method='POST',
                              location_id='4dd4d168-11f2-48c4-83e8-756fa0de027c',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('{GraphSubject}', self._unwrap_collection(response))

    def create_user(self, creation_context, group_descriptors=None):
        """CreateUser.
        [Preview API] Materialize an existing AAD or MSA user into the VSTS account.
        :param :class:`<GraphUserCreationContext> <graph.v4_1.models.GraphUserCreationContext>` creation_context: The subset of the full graph user used to uniquely find the graph subject in an external provider.
        :param [str] group_descriptors: A comma separated list of descriptors of groups you want the graph user to join
        :rtype: :class:`<GraphUser> <graph.v4_1.models.GraphUser>`
        """
        query_parameters = {}
        if group_descriptors is not None:
            group_descriptors = ",".join(group_descriptors)
            query_parameters['groupDescriptors'] = self._serialize.query('group_descriptors', group_descriptors, 'str')
        content = self._serialize.body(creation_context, 'GraphUserCreationContext')
        response = self._send(http_method='POST',
                              location_id='005e26ec-6b77-4e4f-a986-b3827bf241f5',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GraphUser', response)

    def delete_user(self, user_descriptor):
        """DeleteUser.
        [Preview API] Disables a user.
        :param str user_descriptor: The descriptor of the user to delete.
        """
        route_values = {}
        if user_descriptor is not None:
            route_values['userDescriptor'] = self._serialize.url('user_descriptor', user_descriptor, 'str')
        self._send(http_method='DELETE',
                   location_id='005e26ec-6b77-4e4f-a986-b3827bf241f5',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_user(self, user_descriptor):
        """GetUser.
        [Preview API] Get a user by its descriptor.
        :param str user_descriptor: The descriptor of the desired user.
        :rtype: :class:`<GraphUser> <graph.v4_1.models.GraphUser>`
        """
        route_values = {}
        if user_descriptor is not None:
            route_values['userDescriptor'] = self._serialize.url('user_descriptor', user_descriptor, 'str')
        response = self._send(http_method='GET',
                              location_id='005e26ec-6b77-4e4f-a986-b3827bf241f5',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GraphUser', response)

    def list_users(self, subject_types=None, continuation_token=None):
        """ListUsers.
        [Preview API] Get a list of all users in a given scope.
        :param [str] subject_types: A comma separated list of user subject subtypes to reduce the retrieved results, e.g. msa’, ‘aad’, ‘svc’ (service identity), ‘imp’ (imported identity), etc.
        :param str continuation_token: An opaque data blob that allows the next page of data to resume immediately after where the previous page ended. The only reliable way to know if there is more data left is the presence of a continuation token.
        :rtype: :class:`<PagedGraphUsers> <graph.v4_1.models.PagedGraphUsers>`
        """
        query_parameters = {}
        if subject_types is not None:
            subject_types = ",".join(subject_types)
            query_parameters['subjectTypes'] = self._serialize.query('subject_types', subject_types, 'str')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'str')
        response = self._send(http_method='GET',
                              location_id='005e26ec-6b77-4e4f-a986-b3827bf241f5',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        response_object = models.PagedGraphUsers()
        response_object.graph_users = self._deserialize('[GraphUser]', self._unwrap_collection(response))
        response_object.continuation_token = response.headers.get('X-MS-ContinuationToken')
        return response_object

