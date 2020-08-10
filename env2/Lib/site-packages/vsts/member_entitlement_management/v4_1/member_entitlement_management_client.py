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


class MemberEntitlementManagementClient(VssClient):
    """MemberEntitlementManagement
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(MemberEntitlementManagementClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '68ddce18-2501-45f1-a17b-7931a9922690'

    def add_group_entitlement(self, group_entitlement, rule_option=None):
        """AddGroupEntitlement.
        [Preview API] Create a group entitlement with license rule, extension rule.
        :param :class:`<GroupEntitlement> <member-entitlement-management.v4_1.models.GroupEntitlement>` group_entitlement: GroupEntitlement object specifying License Rule, Extensions Rule for the group. Based on the rules the members of the group will be given licenses and extensions. The Group Entitlement can be used to add the group to another project level groups
        :param str rule_option: RuleOption [ApplyGroupRule/TestApplyGroupRule] - specifies if the rules defined in group entitlement should be created and applied to it’s members (default option) or just be tested
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_1.models.GroupEntitlementOperationReference>`
        """
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        content = self._serialize.body(group_entitlement, 'GroupEntitlement')
        response = self._send(http_method='POST',
                              location_id='2280bffa-58a2-49da-822e-0764a1bb44f7',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GroupEntitlementOperationReference', response)

    def delete_group_entitlement(self, group_id, rule_option=None, remove_group_membership=None):
        """DeleteGroupEntitlement.
        [Preview API] Delete a group entitlement.
        :param str group_id: ID of the group to delete.
        :param str rule_option: RuleOption [ApplyGroupRule/TestApplyGroupRule] - specifies if the rules defined in group entitlement should be deleted and the changes are applied to it’s members (default option) or just be tested
        :param bool remove_group_membership: Optional parameter that specifies whether the group with the given ID should be removed from all other groups
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_1.models.GroupEntitlementOperationReference>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        if remove_group_membership is not None:
            query_parameters['removeGroupMembership'] = self._serialize.query('remove_group_membership', remove_group_membership, 'bool')
        response = self._send(http_method='DELETE',
                              location_id='2280bffa-58a2-49da-822e-0764a1bb44f7',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GroupEntitlementOperationReference', response)

    def get_group_entitlement(self, group_id):
        """GetGroupEntitlement.
        [Preview API] Get a group entitlement.
        :param str group_id: ID of the group.
        :rtype: :class:`<GroupEntitlement> <member-entitlement-management.v4_1.models.GroupEntitlement>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        response = self._send(http_method='GET',
                              location_id='2280bffa-58a2-49da-822e-0764a1bb44f7',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('GroupEntitlement', response)

    def get_group_entitlements(self):
        """GetGroupEntitlements.
        [Preview API] Get the group entitlements for an account.
        :rtype: [GroupEntitlement]
        """
        response = self._send(http_method='GET',
                              location_id='2280bffa-58a2-49da-822e-0764a1bb44f7',
                              version='4.1-preview.1')
        return self._deserialize('[GroupEntitlement]', self._unwrap_collection(response))

    def update_group_entitlement(self, document, group_id, rule_option=None):
        """UpdateGroupEntitlement.
        [Preview API] Update entitlements (License Rule, Extensions Rule, Project memberships etc.) for a group.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_1.models.[JsonPatchOperation]>` document: JsonPatchDocument containing the operations to perform on the group.
        :param str group_id: ID of the group.
        :param str rule_option: RuleOption [ApplyGroupRule/TestApplyGroupRule] - specifies if the rules defined in group entitlement should be updated and the changes are applied to it’s members (default option) or just be tested
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_1.models.GroupEntitlementOperationReference>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='2280bffa-58a2-49da-822e-0764a1bb44f7',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('GroupEntitlementOperationReference', response)

    def add_member_to_group(self, group_id, member_id):
        """AddMemberToGroup.
        [Preview API] Add a member to a Group.
        :param str group_id: Id of the Group.
        :param str member_id: Id of the member to add.
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        self._send(http_method='PUT',
                   location_id='45a36e53-5286-4518-aa72-2d29f7acc5d8',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_group_members(self, group_id, max_results=None, paging_token=None):
        """GetGroupMembers.
        [Preview API] Get direct members of a Group.
        :param str group_id: Id of the Group.
        :param int max_results: Maximum number of results to retrieve.
        :param str paging_token: Paging Token from the previous page fetched. If the 'pagingToken' is null, the results would be fetched from the begining of the Members List.
        :rtype: :class:`<PagedGraphMemberList> <member-entitlement-management.v4_1.models.PagedGraphMemberList>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if max_results is not None:
            query_parameters['maxResults'] = self._serialize.query('max_results', max_results, 'int')
        if paging_token is not None:
            query_parameters['pagingToken'] = self._serialize.query('paging_token', paging_token, 'str')
        response = self._send(http_method='GET',
                              location_id='45a36e53-5286-4518-aa72-2d29f7acc5d8',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('PagedGraphMemberList', response)

    def remove_member_from_group(self, group_id, member_id):
        """RemoveMemberFromGroup.
        [Preview API] Remove a member from a Group.
        :param str group_id: Id of the group.
        :param str member_id: Id of the member to remove.
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        self._send(http_method='DELETE',
                   location_id='45a36e53-5286-4518-aa72-2d29f7acc5d8',
                   version='4.1-preview.1',
                   route_values=route_values)

    def add_user_entitlement(self, user_entitlement):
        """AddUserEntitlement.
        [Preview API] Add a user, assign license and extensions and make them a member of a project group in an account.
        :param :class:`<UserEntitlement> <member-entitlement-management.v4_1.models.UserEntitlement>` user_entitlement: UserEntitlement object specifying License, Extensions and Project/Team groups the user should be added to.
        :rtype: :class:`<UserEntitlementsPostResponse> <member-entitlement-management.v4_1.models.UserEntitlementsPostResponse>`
        """
        content = self._serialize.body(user_entitlement, 'UserEntitlement')
        response = self._send(http_method='POST',
                              location_id='387f832c-dbf2-4643-88e9-c1aa94dbb737',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('UserEntitlementsPostResponse', response)

    def get_user_entitlements(self, top=None, skip=None, filter=None, select=None):
        """GetUserEntitlements.
        [Preview API] Get a paged set of user entitlements matching the filter criteria. If no filter is is passed, a page from all the account users is returned.
        :param int top: Maximum number of the user entitlements to return. Max value is 10000. Default value is 100
        :param int skip: Offset: Number of records to skip. Default value is 0
        :param str filter: Comma (",") separated list of properties and their values to filter on. Currently, the API only supports filtering by ExtensionId. An example parameter would be filter=extensionId eq search.
        :param str select: Comma (",") separated list of properties to select in the result entitlements. names of the properties are - 'Projects, 'Extensions' and 'Grouprules'.
        :rtype: [UserEntitlement]
        """
        query_parameters = {}
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['skip'] = self._serialize.query('skip', skip, 'int')
        if filter is not None:
            query_parameters['filter'] = self._serialize.query('filter', filter, 'str')
        if select is not None:
            query_parameters['select'] = self._serialize.query('select', select, 'str')
        response = self._send(http_method='GET',
                              location_id='387f832c-dbf2-4643-88e9-c1aa94dbb737',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[UserEntitlement]', self._unwrap_collection(response))

    def update_user_entitlements(self, document, do_not_send_invite_for_new_users=None):
        """UpdateUserEntitlements.
        [Preview API] Edit the entitlements (License, Extensions, Projects, Teams etc) for one or more users.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_1.models.[JsonPatchOperation]>` document: JsonPatchDocument containing the operations to perform.
        :param bool do_not_send_invite_for_new_users: Whether to send email invites to new users or not
        :rtype: :class:`<UserEntitlementOperationReference> <member-entitlement-management.v4_1.models.UserEntitlementOperationReference>`
        """
        query_parameters = {}
        if do_not_send_invite_for_new_users is not None:
            query_parameters['doNotSendInviteForNewUsers'] = self._serialize.query('do_not_send_invite_for_new_users', do_not_send_invite_for_new_users, 'bool')
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='387f832c-dbf2-4643-88e9-c1aa94dbb737',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('UserEntitlementOperationReference', response)

    def delete_user_entitlement(self, user_id):
        """DeleteUserEntitlement.
        [Preview API] Delete a user from the account.
        :param str user_id: ID of the user.
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        self._send(http_method='DELETE',
                   location_id='8480c6eb-ce60-47e9-88df-eca3c801638b',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_user_entitlement(self, user_id):
        """GetUserEntitlement.
        [Preview API] Get User Entitlement for a user.
        :param str user_id: ID of the user.
        :rtype: :class:`<UserEntitlement> <member-entitlement-management.v4_1.models.UserEntitlement>`
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        response = self._send(http_method='GET',
                              location_id='8480c6eb-ce60-47e9-88df-eca3c801638b',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('UserEntitlement', response)

    def update_user_entitlement(self, document, user_id):
        """UpdateUserEntitlement.
        [Preview API] Edit the entitlements (License, Extensions, Projects, Teams etc) for a user.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_1.models.[JsonPatchOperation]>` document: JsonPatchDocument containing the operations to perform on the user.
        :param str user_id: ID of the user.
        :rtype: :class:`<UserEntitlementsPatchResponse> <member-entitlement-management.v4_1.models.UserEntitlementsPatchResponse>`
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='8480c6eb-ce60-47e9-88df-eca3c801638b',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('UserEntitlementsPatchResponse', response)

    def get_users_summary(self, select=None):
        """GetUsersSummary.
        [Preview API] Get summary of Licenses, Extension, Projects, Groups and their assignments in the collection.
        :param str select: Comma (",") separated list of properties to select. Supported property names are {AccessLevels, Licenses, Extensions, Projects, Groups}.
        :rtype: :class:`<UsersSummary> <member-entitlement-management.v4_1.models.UsersSummary>`
        """
        query_parameters = {}
        if select is not None:
            query_parameters['select'] = self._serialize.query('select', select, 'str')
        response = self._send(http_method='GET',
                              location_id='5ae55b13-c9dd-49d1-957e-6e76c152e3d9',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('UsersSummary', response)

