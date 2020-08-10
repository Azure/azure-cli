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


class SecurityClient(VssClient):
    """Security
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(SecurityClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def remove_access_control_entries(self, security_namespace_id, token=None, descriptors=None):
        """RemoveAccessControlEntries.
        :param str security_namespace_id:
        :param str token:
        :param str descriptors:
        :rtype: bool
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        query_parameters = {}
        if token is not None:
            query_parameters['token'] = self._serialize.query('token', token, 'str')
        if descriptors is not None:
            query_parameters['descriptors'] = self._serialize.query('descriptors', descriptors, 'str')
        response = self._send(http_method='DELETE',
                              location_id='ac08c8ff-4323-4b08-af90-bcd018d380ce',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('bool', response)

    def set_access_control_entries(self, container, security_namespace_id):
        """SetAccessControlEntries.
        :param :class:`<object> <security.v4_0.models.object>` container:
        :param str security_namespace_id:
        :rtype: [AccessControlEntry]
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        content = self._serialize.body(container, 'object')
        response = self._send(http_method='POST',
                              location_id='ac08c8ff-4323-4b08-af90-bcd018d380ce',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[AccessControlEntry]', self._unwrap_collection(response))

    def query_access_control_lists(self, security_namespace_id, token=None, descriptors=None, include_extended_info=None, recurse=None):
        """QueryAccessControlLists.
        :param str security_namespace_id:
        :param str token:
        :param str descriptors:
        :param bool include_extended_info:
        :param bool recurse:
        :rtype: [AccessControlList]
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        query_parameters = {}
        if token is not None:
            query_parameters['token'] = self._serialize.query('token', token, 'str')
        if descriptors is not None:
            query_parameters['descriptors'] = self._serialize.query('descriptors', descriptors, 'str')
        if include_extended_info is not None:
            query_parameters['includeExtendedInfo'] = self._serialize.query('include_extended_info', include_extended_info, 'bool')
        if recurse is not None:
            query_parameters['recurse'] = self._serialize.query('recurse', recurse, 'bool')
        response = self._send(http_method='GET',
                              location_id='18a2ad18-7571-46ae-bec7-0c7da1495885',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[AccessControlList]', self._unwrap_collection(response))

    def remove_access_control_lists(self, security_namespace_id, tokens=None, recurse=None):
        """RemoveAccessControlLists.
        :param str security_namespace_id:
        :param str tokens:
        :param bool recurse:
        :rtype: bool
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        query_parameters = {}
        if tokens is not None:
            query_parameters['tokens'] = self._serialize.query('tokens', tokens, 'str')
        if recurse is not None:
            query_parameters['recurse'] = self._serialize.query('recurse', recurse, 'bool')
        response = self._send(http_method='DELETE',
                              location_id='18a2ad18-7571-46ae-bec7-0c7da1495885',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('bool', response)

    def set_access_control_lists(self, access_control_lists, security_namespace_id):
        """SetAccessControlLists.
        :param :class:`<VssJsonCollectionWrapper> <security.v4_0.models.VssJsonCollectionWrapper>` access_control_lists:
        :param str security_namespace_id:
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        content = self._serialize.body(access_control_lists, 'VssJsonCollectionWrapper')
        self._send(http_method='POST',
                   location_id='18a2ad18-7571-46ae-bec7-0c7da1495885',
                   version='4.0',
                   route_values=route_values,
                   content=content)

    def has_permissions_batch(self, eval_batch):
        """HasPermissionsBatch.
        Perform a batch of "has permission" checks. This methods does not aggregate the results nor does it shortcircut if one of the permissions evaluates to false.
        :param :class:`<PermissionEvaluationBatch> <security.v4_0.models.PermissionEvaluationBatch>` eval_batch:
        :rtype: :class:`<PermissionEvaluationBatch> <security.v4_0.models.PermissionEvaluationBatch>`
        """
        content = self._serialize.body(eval_batch, 'PermissionEvaluationBatch')
        response = self._send(http_method='POST',
                              location_id='cf1faa59-1b63-4448-bf04-13d981a46f5d',
                              version='4.0',
                              content=content)
        return self._deserialize('PermissionEvaluationBatch', response)

    def has_permissions(self, security_namespace_id, permissions=None, tokens=None, always_allow_administrators=None, delimiter=None):
        """HasPermissions.
        :param str security_namespace_id:
        :param int permissions:
        :param str tokens:
        :param bool always_allow_administrators:
        :param str delimiter:
        :rtype: [bool]
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        if permissions is not None:
            route_values['permissions'] = self._serialize.url('permissions', permissions, 'int')
        query_parameters = {}
        if tokens is not None:
            query_parameters['tokens'] = self._serialize.query('tokens', tokens, 'str')
        if always_allow_administrators is not None:
            query_parameters['alwaysAllowAdministrators'] = self._serialize.query('always_allow_administrators', always_allow_administrators, 'bool')
        if delimiter is not None:
            query_parameters['delimiter'] = self._serialize.query('delimiter', delimiter, 'str')
        response = self._send(http_method='GET',
                              location_id='dd3b8bd6-c7fc-4cbd-929a-933d9c011c9d',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[bool]', self._unwrap_collection(response))

    def remove_permission(self, security_namespace_id, permissions=None, token=None, descriptor=None):
        """RemovePermission.
        :param str security_namespace_id:
        :param int permissions:
        :param str token:
        :param str descriptor:
        :rtype: :class:`<AccessControlEntry> <security.v4_0.models.AccessControlEntry>`
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        if permissions is not None:
            route_values['permissions'] = self._serialize.url('permissions', permissions, 'int')
        query_parameters = {}
        if token is not None:
            query_parameters['token'] = self._serialize.query('token', token, 'str')
        if descriptor is not None:
            query_parameters['descriptor'] = self._serialize.query('descriptor', descriptor, 'str')
        response = self._send(http_method='DELETE',
                              location_id='dd3b8bd6-c7fc-4cbd-929a-933d9c011c9d',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('AccessControlEntry', response)

    def query_security_namespaces(self, security_namespace_id, local_only=None):
        """QuerySecurityNamespaces.
        :param str security_namespace_id:
        :param bool local_only:
        :rtype: [SecurityNamespaceDescription]
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        query_parameters = {}
        if local_only is not None:
            query_parameters['localOnly'] = self._serialize.query('local_only', local_only, 'bool')
        response = self._send(http_method='GET',
                              location_id='ce7b9f95-fde9-4be8-a86d-83b366f0b87a',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[SecurityNamespaceDescription]', self._unwrap_collection(response))

    def set_inherit_flag(self, container, security_namespace_id):
        """SetInheritFlag.
        :param :class:`<object> <security.v4_0.models.object>` container:
        :param str security_namespace_id:
        """
        route_values = {}
        if security_namespace_id is not None:
            route_values['securityNamespaceId'] = self._serialize.url('security_namespace_id', security_namespace_id, 'str')
        content = self._serialize.body(container, 'object')
        self._send(http_method='POST',
                   location_id='ce7b9f95-fde9-4be8-a86d-83b366f0b87a',
                   version='4.0',
                   route_values=route_values,
                   content=content)

