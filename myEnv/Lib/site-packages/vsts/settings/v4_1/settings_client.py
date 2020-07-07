# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient


class SettingsClient(VssClient):
    """Settings
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(SettingsClient, self).__init__(base_url, creds)
        self._serialize = Serializer()
        self._deserialize = Deserializer()

    resource_area_identifier = None

    def get_entries(self, user_scope, key=None):
        """GetEntries.
        [Preview API] Get all setting entries for the given user/all-users scope
        :param str user_scope: User-Scope at which to get the value. Should be "me" for the current user or "host" for all users.
        :param str key: Optional key under which to filter all the entries
        :rtype: {object}
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        if key is not None:
            route_values['key'] = self._serialize.url('key', key, 'str')
        response = self._send(http_method='GET',
                              location_id='cd006711-163d-4cd4-a597-b05bad2556ff',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('{object}', self._unwrap_collection(response))

    def remove_entries(self, user_scope, key):
        """RemoveEntries.
        [Preview API] Remove the entry or entries under the specified path
        :param str user_scope: User-Scope at which to remove the value. Should be "me" for the current user or "host" for all users.
        :param str key: Root key of the entry or entries to remove
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        if key is not None:
            route_values['key'] = self._serialize.url('key', key, 'str')
        self._send(http_method='DELETE',
                   location_id='cd006711-163d-4cd4-a597-b05bad2556ff',
                   version='4.1-preview.1',
                   route_values=route_values)

    def set_entries(self, entries, user_scope):
        """SetEntries.
        [Preview API] Set the specified setting entry values for the given user/all-users scope
        :param {object} entries: The entries to set
        :param str user_scope: User-Scope at which to set the values. Should be "me" for the current user or "host" for all users.
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        content = self._serialize.body(entries, '{object}')
        self._send(http_method='PATCH',
                   location_id='cd006711-163d-4cd4-a597-b05bad2556ff',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

    def get_entries_for_scope(self, user_scope, scope_name, scope_value, key=None):
        """GetEntriesForScope.
        [Preview API] Get all setting entries for the given named scope
        :param str user_scope: User-Scope at which to get the value. Should be "me" for the current user or "host" for all users.
        :param str scope_name: Scope at which to get the setting for (e.g. "project" or "team")
        :param str scope_value: Value of the scope (e.g. the project or team id)
        :param str key: Optional key under which to filter all the entries
        :rtype: {object}
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        if scope_name is not None:
            route_values['scopeName'] = self._serialize.url('scope_name', scope_name, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if key is not None:
            route_values['key'] = self._serialize.url('key', key, 'str')
        response = self._send(http_method='GET',
                              location_id='4cbaafaf-e8af-4570-98d1-79ee99c56327',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('{object}', self._unwrap_collection(response))

    def remove_entries_for_scope(self, user_scope, scope_name, scope_value, key):
        """RemoveEntriesForScope.
        [Preview API] Remove the entry or entries under the specified path
        :param str user_scope: User-Scope at which to remove the value. Should be "me" for the current user or "host" for all users.
        :param str scope_name: Scope at which to get the setting for (e.g. "project" or "team")
        :param str scope_value: Value of the scope (e.g. the project or team id)
        :param str key: Root key of the entry or entries to remove
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        if scope_name is not None:
            route_values['scopeName'] = self._serialize.url('scope_name', scope_name, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if key is not None:
            route_values['key'] = self._serialize.url('key', key, 'str')
        self._send(http_method='DELETE',
                   location_id='4cbaafaf-e8af-4570-98d1-79ee99c56327',
                   version='4.1-preview.1',
                   route_values=route_values)

    def set_entries_for_scope(self, entries, user_scope, scope_name, scope_value):
        """SetEntriesForScope.
        [Preview API] Set the specified entries for the given named scope
        :param {object} entries: The entries to set
        :param str user_scope: User-Scope at which to set the values. Should be "me" for the current user or "host" for all users.
        :param str scope_name: Scope at which to set the settings on (e.g. "project" or "team")
        :param str scope_value: Value of the scope (e.g. the project or team id)
        """
        route_values = {}
        if user_scope is not None:
            route_values['userScope'] = self._serialize.url('user_scope', user_scope, 'str')
        if scope_name is not None:
            route_values['scopeName'] = self._serialize.url('scope_name', scope_name, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        content = self._serialize.body(entries, '{object}')
        self._send(http_method='PATCH',
                   location_id='4cbaafaf-e8af-4570-98d1-79ee99c56327',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

