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
        [Preview API] Used to add members to a project in an account. It adds them to groups, assigns licenses, and assigns extensions.
        :param :class:`<GroupEntitlement> <member-entitlement-management.v4_0.models.GroupEntitlement>` group_entitlement: Member model for where to add the member and what licenses and extensions they should receive.
        :param str rule_option:
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_0.models.GroupEntitlementOperationReference>`
        """
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        content = self._serialize.body(group_entitlement, 'GroupEntitlement')
        response = self._send(http_method='POST',
                              location_id='ec7fb08f-5dcc-481c-9bf6-122001b1caa6',
                              version='4.0-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GroupEntitlementOperationReference', response)

    def delete_group_entitlement(self, group_id, rule_option=None):
        """DeleteGroupEntitlement.
        [Preview API] Deletes members from an account
        :param str group_id: memberId of the member to be removed.
        :param str rule_option:
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_0.models.GroupEntitlementOperationReference>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        response = self._send(http_method='DELETE',
                              location_id='ec7fb08f-5dcc-481c-9bf6-122001b1caa6',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GroupEntitlementOperationReference', response)

    def get_group_entitlement(self, group_id):
        """GetGroupEntitlement.
        [Preview API] Used to get a group entitlement and its current rules
        :param str group_id:
        :rtype: :class:`<GroupEntitlement> <member-entitlement-management.v4_0.models.GroupEntitlement>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        response = self._send(http_method='GET',
                              location_id='ec7fb08f-5dcc-481c-9bf6-122001b1caa6',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GroupEntitlement', response)

    def get_group_entitlements(self):
        """GetGroupEntitlements.
        [Preview API] Used to get group entitlement information in an account
        :rtype: [GroupEntitlement]
        """
        response = self._send(http_method='GET',
                              location_id='ec7fb08f-5dcc-481c-9bf6-122001b1caa6',
                              version='4.0-preview.1')
        return self._deserialize('[GroupEntitlement]', self._unwrap_collection(response))

    def update_group_entitlement(self, document, group_id, rule_option=None):
        """UpdateGroupEntitlement.
        [Preview API] Used to edit a member in an account. Edits groups, licenses, and extensions.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_0.models.[JsonPatchOperation]>` document: document of operations to be used
        :param str group_id: member Id of the member to be edit
        :param str rule_option:
        :rtype: :class:`<GroupEntitlementOperationReference> <member-entitlement-management.v4_0.models.GroupEntitlementOperationReference>`
        """
        route_values = {}
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if rule_option is not None:
            query_parameters['ruleOption'] = self._serialize.query('rule_option', rule_option, 'str')
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='ec7fb08f-5dcc-481c-9bf6-122001b1caa6',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('GroupEntitlementOperationReference', response)

    def add_member_entitlement(self, member_entitlement):
        """AddMemberEntitlement.
        [Preview API] Used to add members to a project in an account. It adds them to project groups, assigns licenses, and assigns extensions.
        :param :class:`<MemberEntitlement> <member-entitlement-management.v4_0.models.MemberEntitlement>` member_entitlement: Member model for where to add the member and what licenses and extensions they should receive.
        :rtype: :class:`<MemberEntitlementsPostResponse> <member-entitlement-management.v4_0.models.MemberEntitlementsPostResponse>`
        """
        content = self._serialize.body(member_entitlement, 'MemberEntitlement')
        response = self._send(http_method='POST',
                              location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('MemberEntitlementsPostResponse', response)

    def delete_member_entitlement(self, member_id):
        """DeleteMemberEntitlement.
        [Preview API] Deletes members from an account
        :param str member_id: memberId of the member to be removed.
        """
        route_values = {}
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        self._send(http_method='DELETE',
                   location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_member_entitlement(self, member_id):
        """GetMemberEntitlement.
        [Preview API] Used to get member entitlement information in an account
        :param str member_id:
        :rtype: :class:`<MemberEntitlement> <member-entitlement-management.v4_0.models.MemberEntitlement>`
        """
        route_values = {}
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        response = self._send(http_method='GET',
                              location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('MemberEntitlement', response)

    def get_member_entitlements(self, top, skip, filter=None, select=None):
        """GetMemberEntitlements.
        [Preview API] Used to get member entitlement information in an account
        :param int top:
        :param int skip:
        :param str filter:
        :param str select:
        :rtype: [MemberEntitlement]
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
                              location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[MemberEntitlement]', self._unwrap_collection(response))

    def update_member_entitlement(self, document, member_id):
        """UpdateMemberEntitlement.
        [Preview API] Used to edit a member in an account. Edits groups, licenses, and extensions.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_0.models.[JsonPatchOperation]>` document: document of operations to be used
        :param str member_id: member Id of the member to be edit
        :rtype: :class:`<MemberEntitlementsPatchResponse> <member-entitlement-management.v4_0.models.MemberEntitlementsPatchResponse>`
        """
        route_values = {}
        if member_id is not None:
            route_values['memberId'] = self._serialize.url('member_id', member_id, 'str')
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('MemberEntitlementsPatchResponse', response)

    def update_member_entitlements(self, document):
        """UpdateMemberEntitlements.
        [Preview API] Used to edit multiple members in an account. Edits groups, licenses, and extensions.
        :param :class:`<[JsonPatchOperation]> <member-entitlement-management.v4_0.models.[JsonPatchOperation]>` document: JsonPatch document
        :rtype: :class:`<MemberEntitlementOperationReference> <member-entitlement-management.v4_0.models.MemberEntitlementOperationReference>`
        """
        content = self._serialize.body(document, '[JsonPatchOperation]')
        response = self._send(http_method='PATCH',
                              location_id='1e8cabfb-1fda-461e-860f-eeeae54d06bb',
                              version='4.0-preview.1',
                              content=content,
                              media_type='application/json-patch+json')
        return self._deserialize('MemberEntitlementOperationReference', response)

