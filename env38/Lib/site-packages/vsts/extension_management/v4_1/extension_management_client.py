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


class ExtensionManagementClient(VssClient):
    """ExtensionManagement
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ExtensionManagementClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '6c2b0933-3600-42ae-bf8b-93d4f7e83594'

    def get_installed_extensions(self, include_disabled_extensions=None, include_errors=None, asset_types=None, include_installation_issues=None):
        """GetInstalledExtensions.
        [Preview API] List the installed extensions in the account / project collection.
        :param bool include_disabled_extensions: If true (the default), include disabled extensions in the results.
        :param bool include_errors: If true, include installed extensions with errors.
        :param [str] asset_types:
        :param bool include_installation_issues:
        :rtype: [InstalledExtension]
        """
        query_parameters = {}
        if include_disabled_extensions is not None:
            query_parameters['includeDisabledExtensions'] = self._serialize.query('include_disabled_extensions', include_disabled_extensions, 'bool')
        if include_errors is not None:
            query_parameters['includeErrors'] = self._serialize.query('include_errors', include_errors, 'bool')
        if asset_types is not None:
            asset_types = ":".join(asset_types)
            query_parameters['assetTypes'] = self._serialize.query('asset_types', asset_types, 'str')
        if include_installation_issues is not None:
            query_parameters['includeInstallationIssues'] = self._serialize.query('include_installation_issues', include_installation_issues, 'bool')
        response = self._send(http_method='GET',
                              location_id='275424d0-c844-4fe2-bda6-04933a1357d8',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[InstalledExtension]', self._unwrap_collection(response))

    def update_installed_extension(self, extension):
        """UpdateInstalledExtension.
        [Preview API] Update an installed extension. Typically this API is used to enable or disable an extension.
        :param :class:`<InstalledExtension> <extension-management.v4_1.models.InstalledExtension>` extension:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_1.models.InstalledExtension>`
        """
        content = self._serialize.body(extension, 'InstalledExtension')
        response = self._send(http_method='PATCH',
                              location_id='275424d0-c844-4fe2-bda6-04933a1357d8',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('InstalledExtension', response)

    def get_installed_extension_by_name(self, publisher_name, extension_name, asset_types=None):
        """GetInstalledExtensionByName.
        [Preview API] Get an installed extension by its publisher and extension name.
        :param str publisher_name: Name of the publisher. Example: "fabrikam".
        :param str extension_name: Name of the extension. Example: "ops-tools".
        :param [str] asset_types:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_1.models.InstalledExtension>`
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
                              location_id='fb0da285-f23e-4b56-8b53-3ef5f9f6de66',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('InstalledExtension', response)

    def install_extension_by_name(self, publisher_name, extension_name, version=None):
        """InstallExtensionByName.
        [Preview API] Install the specified extension into the account / project collection.
        :param str publisher_name: Name of the publisher. Example: "fabrikam".
        :param str extension_name: Name of the extension. Example: "ops-tools".
        :param str version:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_1.models.InstalledExtension>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        response = self._send(http_method='POST',
                              location_id='fb0da285-f23e-4b56-8b53-3ef5f9f6de66',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('InstalledExtension', response)

    def uninstall_extension_by_name(self, publisher_name, extension_name, reason=None, reason_code=None):
        """UninstallExtensionByName.
        [Preview API] Uninstall the specified extension from the account / project collection.
        :param str publisher_name: Name of the publisher. Example: "fabrikam".
        :param str extension_name: Name of the extension. Example: "ops-tools".
        :param str reason:
        :param str reason_code:
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        query_parameters = {}
        if reason is not None:
            query_parameters['reason'] = self._serialize.query('reason', reason, 'str')
        if reason_code is not None:
            query_parameters['reasonCode'] = self._serialize.query('reason_code', reason_code, 'str')
        self._send(http_method='DELETE',
                   location_id='fb0da285-f23e-4b56-8b53-3ef5f9f6de66',
                   version='4.1-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters)

