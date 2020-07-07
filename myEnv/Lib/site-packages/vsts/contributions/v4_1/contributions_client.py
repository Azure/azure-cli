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


class ContributionsClient(VssClient):
    """Contributions
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ContributionsClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '8477aec9-a4c7-4bd4-a456-ba4c53c989cb'

    def query_contribution_nodes(self, query):
        """QueryContributionNodes.
        [Preview API] Query for contribution nodes and provider details according the parameters in the passed in query object.
        :param :class:`<ContributionNodeQuery> <contributions.v4_1.models.ContributionNodeQuery>` query:
        :rtype: :class:`<ContributionNodeQueryResult> <contributions.v4_1.models.ContributionNodeQueryResult>`
        """
        content = self._serialize.body(query, 'ContributionNodeQuery')
        response = self._send(http_method='POST',
                              location_id='db7f2146-2309-4cee-b39c-c767777a1c55',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('ContributionNodeQueryResult', response)

    def query_data_providers(self, query, scope_name=None, scope_value=None):
        """QueryDataProviders.
        [Preview API]
        :param :class:`<DataProviderQuery> <contributions.v4_1.models.DataProviderQuery>` query:
        :param str scope_name:
        :param str scope_value:
        :rtype: :class:`<DataProviderResult> <contributions.v4_1.models.DataProviderResult>`
        """
        route_values = {}
        if scope_name is not None:
            route_values['scopeName'] = self._serialize.url('scope_name', scope_name, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        content = self._serialize.body(query, 'DataProviderQuery')
        response = self._send(http_method='POST',
                              location_id='738368db-35ee-4b85-9f94-77ed34af2b0d',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('DataProviderResult', response)

    def get_installed_extensions(self, contribution_ids=None, include_disabled_apps=None, asset_types=None):
        """GetInstalledExtensions.
        [Preview API]
        :param [str] contribution_ids:
        :param bool include_disabled_apps:
        :param [str] asset_types:
        :rtype: [InstalledExtension]
        """
        query_parameters = {}
        if contribution_ids is not None:
            contribution_ids = ";".join(contribution_ids)
            query_parameters['contributionIds'] = self._serialize.query('contribution_ids', contribution_ids, 'str')
        if include_disabled_apps is not None:
            query_parameters['includeDisabledApps'] = self._serialize.query('include_disabled_apps', include_disabled_apps, 'bool')
        if asset_types is not None:
            asset_types = ":".join(asset_types)
            query_parameters['assetTypes'] = self._serialize.query('asset_types', asset_types, 'str')
        response = self._send(http_method='GET',
                              location_id='2648442b-fd63-4b9a-902f-0c913510f139',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[InstalledExtension]', self._unwrap_collection(response))

    def get_installed_extension_by_name(self, publisher_name, extension_name, asset_types=None):
        """GetInstalledExtensionByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param [str] asset_types:
        :rtype: :class:`<InstalledExtension> <contributions.v4_1.models.InstalledExtension>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        query_parameters = {}
        if asset_types is not None:
            asset_types = ":".join(asset_types)
            query_parameters['assetTypes'] = self._serialize.query('asset_types', asset_types, 'str')
        response = self._send(http_method='GET',
                              location_id='3e2f6668-0798-4dcb-b592-bfe2fa57fde2',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('InstalledExtension', response)

