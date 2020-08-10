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

    def get_acquisition_options(self, item_id, test_commerce=None, is_free_or_trial_install=None):
        """GetAcquisitionOptions.
        [Preview API]
        :param str item_id:
        :param bool test_commerce:
        :param bool is_free_or_trial_install:
        :rtype: :class:`<AcquisitionOptions> <extension-management.v4_0.models.AcquisitionOptions>`
        """
        query_parameters = {}
        if item_id is not None:
            query_parameters['itemId'] = self._serialize.query('item_id', item_id, 'str')
        if test_commerce is not None:
            query_parameters['testCommerce'] = self._serialize.query('test_commerce', test_commerce, 'bool')
        if is_free_or_trial_install is not None:
            query_parameters['isFreeOrTrialInstall'] = self._serialize.query('is_free_or_trial_install', is_free_or_trial_install, 'bool')
        response = self._send(http_method='GET',
                              location_id='288dff58-d13b-468e-9671-0fb754e9398c',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('AcquisitionOptions', response)

    def request_acquisition(self, acquisition_request):
        """RequestAcquisition.
        [Preview API]
        :param :class:`<ExtensionAcquisitionRequest> <extension-management.v4_0.models.ExtensionAcquisitionRequest>` acquisition_request:
        :rtype: :class:`<ExtensionAcquisitionRequest> <extension-management.v4_0.models.ExtensionAcquisitionRequest>`
        """
        content = self._serialize.body(acquisition_request, 'ExtensionAcquisitionRequest')
        response = self._send(http_method='POST',
                              location_id='da616457-eed3-4672-92d7-18d21f5c1658',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('ExtensionAcquisitionRequest', response)

    def register_authorization(self, publisher_name, extension_name, registration_id):
        """RegisterAuthorization.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str registration_id:
        :rtype: :class:`<ExtensionAuthorization> <extension-management.v4_0.models.ExtensionAuthorization>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if registration_id is not None:
            route_values['registrationId'] = self._serialize.url('registration_id', registration_id, 'str')
        response = self._send(http_method='PUT',
                              location_id='f21cfc80-d2d2-4248-98bb-7820c74c4606',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('ExtensionAuthorization', response)

    def create_document_by_name(self, doc, publisher_name, extension_name, scope_type, scope_value, collection_name):
        """CreateDocumentByName.
        [Preview API]
        :param :class:`<object> <extension-management.v4_0.models.object>` doc:
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :rtype: :class:`<object> <extension-management.v4_0.models.object>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        content = self._serialize.body(doc, 'object')
        response = self._send(http_method='POST',
                              location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('object', response)

    def delete_document_by_name(self, publisher_name, extension_name, scope_type, scope_value, collection_name, document_id):
        """DeleteDocumentByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :param str document_id:
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        if document_id is not None:
            route_values['documentId'] = self._serialize.url('document_id', document_id, 'str')
        self._send(http_method='DELETE',
                   location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_document_by_name(self, publisher_name, extension_name, scope_type, scope_value, collection_name, document_id):
        """GetDocumentByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :param str document_id:
        :rtype: :class:`<object> <extension-management.v4_0.models.object>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        if document_id is not None:
            route_values['documentId'] = self._serialize.url('document_id', document_id, 'str')
        response = self._send(http_method='GET',
                              location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('object', response)

    def get_documents_by_name(self, publisher_name, extension_name, scope_type, scope_value, collection_name):
        """GetDocumentsByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :rtype: [object]
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        response = self._send(http_method='GET',
                              location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[object]', self._unwrap_collection(response))

    def set_document_by_name(self, doc, publisher_name, extension_name, scope_type, scope_value, collection_name):
        """SetDocumentByName.
        [Preview API]
        :param :class:`<object> <extension-management.v4_0.models.object>` doc:
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :rtype: :class:`<object> <extension-management.v4_0.models.object>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        content = self._serialize.body(doc, 'object')
        response = self._send(http_method='PUT',
                              location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('object', response)

    def update_document_by_name(self, doc, publisher_name, extension_name, scope_type, scope_value, collection_name):
        """UpdateDocumentByName.
        [Preview API]
        :param :class:`<object> <extension-management.v4_0.models.object>` doc:
        :param str publisher_name:
        :param str extension_name:
        :param str scope_type:
        :param str scope_value:
        :param str collection_name:
        :rtype: :class:`<object> <extension-management.v4_0.models.object>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if scope_type is not None:
            route_values['scopeType'] = self._serialize.url('scope_type', scope_type, 'str')
        if scope_value is not None:
            route_values['scopeValue'] = self._serialize.url('scope_value', scope_value, 'str')
        if collection_name is not None:
            route_values['collectionName'] = self._serialize.url('collection_name', collection_name, 'str')
        content = self._serialize.body(doc, 'object')
        response = self._send(http_method='PATCH',
                              location_id='bbe06c18-1c8b-4fcd-b9c6-1535aaab8749',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('object', response)

    def query_collections_by_name(self, collection_query, publisher_name, extension_name):
        """QueryCollectionsByName.
        [Preview API]
        :param :class:`<ExtensionDataCollectionQuery> <extension-management.v4_0.models.ExtensionDataCollectionQuery>` collection_query:
        :param str publisher_name:
        :param str extension_name:
        :rtype: [ExtensionDataCollection]
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        content = self._serialize.body(collection_query, 'ExtensionDataCollectionQuery')
        response = self._send(http_method='POST',
                              location_id='56c331f1-ce53-4318-adfd-4db5c52a7a2e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[ExtensionDataCollection]', self._unwrap_collection(response))

    def get_states(self, include_disabled=None, include_errors=None, include_installation_issues=None):
        """GetStates.
        [Preview API]
        :param bool include_disabled:
        :param bool include_errors:
        :param bool include_installation_issues:
        :rtype: [ExtensionState]
        """
        query_parameters = {}
        if include_disabled is not None:
            query_parameters['includeDisabled'] = self._serialize.query('include_disabled', include_disabled, 'bool')
        if include_errors is not None:
            query_parameters['includeErrors'] = self._serialize.query('include_errors', include_errors, 'bool')
        if include_installation_issues is not None:
            query_parameters['includeInstallationIssues'] = self._serialize.query('include_installation_issues', include_installation_issues, 'bool')
        response = self._send(http_method='GET',
                              location_id='92755d3d-9a8a-42b3-8a4d-87359fe5aa93',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[ExtensionState]', self._unwrap_collection(response))

    def query_extensions(self, query):
        """QueryExtensions.
        [Preview API]
        :param :class:`<InstalledExtensionQuery> <extension-management.v4_0.models.InstalledExtensionQuery>` query:
        :rtype: [InstalledExtension]
        """
        content = self._serialize.body(query, 'InstalledExtensionQuery')
        response = self._send(http_method='POST',
                              location_id='046c980f-1345-4ce2-bf85-b46d10ff4cfd',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('[InstalledExtension]', self._unwrap_collection(response))

    def get_installed_extensions(self, include_disabled_extensions=None, include_errors=None, asset_types=None, include_installation_issues=None):
        """GetInstalledExtensions.
        [Preview API]
        :param bool include_disabled_extensions:
        :param bool include_errors:
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
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[InstalledExtension]', self._unwrap_collection(response))

    def update_installed_extension(self, extension):
        """UpdateInstalledExtension.
        [Preview API]
        :param :class:`<InstalledExtension> <extension-management.v4_0.models.InstalledExtension>` extension:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_0.models.InstalledExtension>`
        """
        content = self._serialize.body(extension, 'InstalledExtension')
        response = self._send(http_method='PATCH',
                              location_id='275424d0-c844-4fe2-bda6-04933a1357d8',
                              version='4.0-preview.1',
                              content=content)
        return self._deserialize('InstalledExtension', response)

    def get_installed_extension_by_name(self, publisher_name, extension_name, asset_types=None):
        """GetInstalledExtensionByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param [str] asset_types:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_0.models.InstalledExtension>`
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
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('InstalledExtension', response)

    def install_extension_by_name(self, publisher_name, extension_name, version=None):
        """InstallExtensionByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str version:
        :rtype: :class:`<InstalledExtension> <extension-management.v4_0.models.InstalledExtension>`
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
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('InstalledExtension', response)

    def uninstall_extension_by_name(self, publisher_name, extension_name, reason=None, reason_code=None):
        """UninstallExtensionByName.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
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
                   version='4.0-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_policies(self, user_id):
        """GetPolicies.
        [Preview API]
        :param str user_id:
        :rtype: :class:`<UserExtensionPolicy> <extension-management.v4_0.models.UserExtensionPolicy>`
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        response = self._send(http_method='GET',
                              location_id='e5cc8c09-407b-4867-8319-2ae3338cbf6f',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('UserExtensionPolicy', response)

    def resolve_request(self, reject_message, publisher_name, extension_name, requester_id, state):
        """ResolveRequest.
        [Preview API]
        :param str reject_message:
        :param str publisher_name:
        :param str extension_name:
        :param str requester_id:
        :param str state:
        :rtype: int
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        if requester_id is not None:
            route_values['requesterId'] = self._serialize.url('requester_id', requester_id, 'str')
        query_parameters = {}
        if state is not None:
            query_parameters['state'] = self._serialize.query('state', state, 'str')
        content = self._serialize.body(reject_message, 'str')
        response = self._send(http_method='PATCH',
                              location_id='aa93e1f3-511c-4364-8b9c-eb98818f2e0b',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('int', response)

    def get_requests(self):
        """GetRequests.
        [Preview API]
        :rtype: [RequestedExtension]
        """
        response = self._send(http_method='GET',
                              location_id='216b978f-b164-424e-ada2-b77561e842b7',
                              version='4.0-preview.1')
        return self._deserialize('[RequestedExtension]', self._unwrap_collection(response))

    def resolve_all_requests(self, reject_message, publisher_name, extension_name, state):
        """ResolveAllRequests.
        [Preview API]
        :param str reject_message:
        :param str publisher_name:
        :param str extension_name:
        :param str state:
        :rtype: int
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        query_parameters = {}
        if state is not None:
            query_parameters['state'] = self._serialize.query('state', state, 'str')
        content = self._serialize.body(reject_message, 'str')
        response = self._send(http_method='PATCH',
                              location_id='ba93e1f3-511c-4364-8b9c-eb98818f2e0b',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('int', response)

    def delete_request(self, publisher_name, extension_name):
        """DeleteRequest.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        self._send(http_method='DELETE',
                   location_id='f5afca1e-a728-4294-aa2d-4af0173431b5',
                   version='4.0-preview.1',
                   route_values=route_values)

    def request_extension(self, publisher_name, extension_name, request_message):
        """RequestExtension.
        [Preview API]
        :param str publisher_name:
        :param str extension_name:
        :param str request_message:
        :rtype: :class:`<RequestedExtension> <extension-management.v4_0.models.RequestedExtension>`
        """
        route_values = {}
        if publisher_name is not None:
            route_values['publisherName'] = self._serialize.url('publisher_name', publisher_name, 'str')
        if extension_name is not None:
            route_values['extensionName'] = self._serialize.url('extension_name', extension_name, 'str')
        content = self._serialize.body(request_message, 'str')
        response = self._send(http_method='POST',
                              location_id='f5afca1e-a728-4294-aa2d-4af0173431b5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('RequestedExtension', response)

    def get_token(self):
        """GetToken.
        [Preview API]
        :rtype: str
        """
        response = self._send(http_method='GET',
                              location_id='3a2e24ed-1d6f-4cb2-9f3b-45a96bbfaf50',
                              version='4.0-preview.1')
        return self._deserialize('str', response)

