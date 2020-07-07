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


class LicensingClient(VssClient):
    """Licensing
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(LicensingClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'c73a23a1-59bb-458c-8ce3-02c83215e015'

    def get_extension_license_usage(self):
        """GetExtensionLicenseUsage.
        [Preview API] Returns Licensing info about paid extensions assigned to user passed into GetExtensionsAssignedToAccount
        :rtype: [AccountLicenseExtensionUsage]
        """
        response = self._send(http_method='GET',
                              location_id='01bce8d3-c130-480f-a332-474ae3f6662e',
                              version='4.1-preview.1')
        return self._deserialize('[AccountLicenseExtensionUsage]', self._unwrap_collection(response))

    def get_certificate(self, **kwargs):
        """GetCertificate.
        [Preview API]
        :rtype: object
        """
        response = self._send(http_method='GET',
                              location_id='2e0dbce7-a327-4bc0-a291-056139393f6d',
                              version='4.1-preview.1',
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_client_rights(self, right_name=None, product_version=None, edition=None, rel_type=None, include_certificate=None, canary=None, machine_id=None):
        """GetClientRights.
        [Preview API]
        :param str right_name:
        :param str product_version:
        :param str edition:
        :param str rel_type:
        :param bool include_certificate:
        :param str canary:
        :param str machine_id:
        :rtype: :class:`<ClientRightsContainer> <licensing.v4_1.models.ClientRightsContainer>`
        """
        route_values = {}
        if right_name is not None:
            route_values['rightName'] = self._serialize.url('right_name', right_name, 'str')
        query_parameters = {}
        if product_version is not None:
            query_parameters['productVersion'] = self._serialize.query('product_version', product_version, 'str')
        if edition is not None:
            query_parameters['edition'] = self._serialize.query('edition', edition, 'str')
        if rel_type is not None:
            query_parameters['relType'] = self._serialize.query('rel_type', rel_type, 'str')
        if include_certificate is not None:
            query_parameters['includeCertificate'] = self._serialize.query('include_certificate', include_certificate, 'bool')
        if canary is not None:
            query_parameters['canary'] = self._serialize.query('canary', canary, 'str')
        if machine_id is not None:
            query_parameters['machineId'] = self._serialize.query('machine_id', machine_id, 'str')
        response = self._send(http_method='GET',
                              location_id='643c72da-eaee-4163-9f07-d748ef5c2a0c',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ClientRightsContainer', response)

    def assign_available_account_entitlement(self, user_id, dont_notify_user=None, origin=None):
        """AssignAvailableAccountEntitlement.
        [Preview API] Assign an available entitilement to a user
        :param str user_id: The user to which to assign the entitilement
        :param bool dont_notify_user:
        :param str origin:
        :rtype: :class:`<AccountEntitlement> <licensing.v4_1.models.AccountEntitlement>`
        """
        query_parameters = {}
        if user_id is not None:
            query_parameters['userId'] = self._serialize.query('user_id', user_id, 'str')
        if dont_notify_user is not None:
            query_parameters['dontNotifyUser'] = self._serialize.query('dont_notify_user', dont_notify_user, 'bool')
        if origin is not None:
            query_parameters['origin'] = self._serialize.query('origin', origin, 'str')
        response = self._send(http_method='POST',
                              location_id='c01e9fd5-0d8c-4d5e-9a68-734bd8da6a38',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('AccountEntitlement', response)

    def get_account_entitlement(self):
        """GetAccountEntitlement.
        [Preview API] Gets the account entitlement of the current user it is mapped to _apis/licensing/entitlements/me so specifically is looking for the user of the request
        :rtype: :class:`<AccountEntitlement> <licensing.v4_1.models.AccountEntitlement>`
        """
        response = self._send(http_method='GET',
                              location_id='c01e9fd5-0d8c-4d5e-9a68-734bd8da6a38',
                              version='4.1-preview.1')
        return self._deserialize('AccountEntitlement', response)

    def get_account_entitlements(self, top=None, skip=None):
        """GetAccountEntitlements.
        [Preview API] Gets top (top) entitlements for users in the account from offset (skip) order by DateCreated ASC
        :param int top: number of accounts to return
        :param int skip: records to skip, null is interpreted as 0
        :rtype: [AccountEntitlement]
        """
        query_parameters = {}
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['skip'] = self._serialize.query('skip', skip, 'int')
        response = self._send(http_method='GET',
                              location_id='ea37be6f-8cd7-48dd-983d-2b72d6e3da0f',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[AccountEntitlement]', self._unwrap_collection(response))

    def assign_account_entitlement_for_user(self, body, user_id, dont_notify_user=None, origin=None):
        """AssignAccountEntitlementForUser.
        [Preview API] Assign an explicit account entitlement
        :param :class:`<AccountEntitlementUpdateModel> <licensing.v4_1.models.AccountEntitlementUpdateModel>` body: The update model for the entitlement
        :param str user_id: The id of the user
        :param bool dont_notify_user:
        :param str origin:
        :rtype: :class:`<AccountEntitlement> <licensing.v4_1.models.AccountEntitlement>`
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        query_parameters = {}
        if dont_notify_user is not None:
            query_parameters['dontNotifyUser'] = self._serialize.query('dont_notify_user', dont_notify_user, 'bool')
        if origin is not None:
            query_parameters['origin'] = self._serialize.query('origin', origin, 'str')
        content = self._serialize.body(body, 'AccountEntitlementUpdateModel')
        response = self._send(http_method='PUT',
                              location_id='6490e566-b299-49a7-a4e4-28749752581f',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('AccountEntitlement', response)

    def delete_user_entitlements(self, user_id):
        """DeleteUserEntitlements.
        [Preview API]
        :param str user_id:
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        self._send(http_method='DELETE',
                   location_id='6490e566-b299-49a7-a4e4-28749752581f',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_account_entitlement_for_user(self, user_id, determine_rights=None):
        """GetAccountEntitlementForUser.
        [Preview API] Get the entitlements for a user
        :param str user_id: The id of the user
        :param bool determine_rights:
        :rtype: :class:`<AccountEntitlement> <licensing.v4_1.models.AccountEntitlement>`
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        query_parameters = {}
        if determine_rights is not None:
            query_parameters['determineRights'] = self._serialize.query('determine_rights', determine_rights, 'bool')
        response = self._send(http_method='GET',
                              location_id='6490e566-b299-49a7-a4e4-28749752581f',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('AccountEntitlement', response)

    def get_account_entitlements_batch(self, user_ids):
        """GetAccountEntitlementsBatch.
        [Preview API] Returns AccountEntitlements that are currently assigned to the given list of users in the account
        :param [str] user_ids: List of user Ids.
        :rtype: [AccountEntitlement]
        """
        route_values = {}
        route_values['action'] = 'GetUsersEntitlements'
        content = self._serialize.body(user_ids, '[str]')
        response = self._send(http_method='POST',
                              location_id='cc3a0130-78ad-4a00-b1ca-49bef42f4656',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[AccountEntitlement]', self._unwrap_collection(response))

    def obtain_available_account_entitlements(self, user_ids):
        """ObtainAvailableAccountEntitlements.
        [Preview API] Returns AccountEntitlements that are currently assigned to the given list of users in the account
        :param [str] user_ids: List of user Ids.
        :rtype: [AccountEntitlement]
        """
        route_values = {}
        route_values['action'] = 'GetAvailableUsersEntitlements'
        content = self._serialize.body(user_ids, '[str]')
        response = self._send(http_method='POST',
                              location_id='cc3a0130-78ad-4a00-b1ca-49bef42f4656',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[AccountEntitlement]', self._unwrap_collection(response))

    def assign_extension_to_all_eligible_users(self, extension_id):
        """AssignExtensionToAllEligibleUsers.
        [Preview API] Assigns the access to the given extension for all eligible users in the account that do not already have access to the extension though bundle or account assignment
        :param str extension_id: The extension id to assign the access to.
        :rtype: [ExtensionOperationResult]
        """
        route_values = {}
        if extension_id is not None:
            route_values['extensionId'] = self._serialize.url('extension_id', extension_id, 'str')
        response = self._send(http_method='PUT',
                              location_id='5434f182-7f32-4135-8326-9340d887c08a',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[ExtensionOperationResult]', self._unwrap_collection(response))

    def get_eligible_users_for_extension(self, extension_id, options):
        """GetEligibleUsersForExtension.
        [Preview API] Returns users that are currently eligible to assign the extension to. the list is filtered based on the value of ExtensionFilterOptions
        :param str extension_id: The extension to check the eligibility of the users for.
        :param str options: The options to filter the list.
        :rtype: [str]
        """
        route_values = {}
        if extension_id is not None:
            route_values['extensionId'] = self._serialize.url('extension_id', extension_id, 'str')
        query_parameters = {}
        if options is not None:
            query_parameters['options'] = self._serialize.query('options', options, 'str')
        response = self._send(http_method='GET',
                              location_id='5434f182-7f32-4135-8326-9340d887c08a',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def get_extension_status_for_users(self, extension_id):
        """GetExtensionStatusForUsers.
        [Preview API] Returns extension assignment status of all account users for the given extension
        :param str extension_id: The extension to check the status of the users for.
        :rtype: {ExtensionAssignmentDetails}
        """
        route_values = {}
        if extension_id is not None:
            route_values['extensionId'] = self._serialize.url('extension_id', extension_id, 'str')
        response = self._send(http_method='GET',
                              location_id='5434f182-7f32-4135-8326-9340d887c08a',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('{ExtensionAssignmentDetails}', self._unwrap_collection(response))

    def assign_extension_to_users(self, body):
        """AssignExtensionToUsers.
        [Preview API] Assigns the access to the given extension for a given list of users
        :param :class:`<ExtensionAssignment> <licensing.v4_1.models.ExtensionAssignment>` body: The extension assignment details.
        :rtype: [ExtensionOperationResult]
        """
        content = self._serialize.body(body, 'ExtensionAssignment')
        response = self._send(http_method='PUT',
                              location_id='8cec75ea-044f-4245-ab0d-a82dafcc85ea',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('[ExtensionOperationResult]', self._unwrap_collection(response))

    def get_extensions_assigned_to_user(self, user_id):
        """GetExtensionsAssignedToUser.
        [Preview API] Returns extensions that are currently assigned to the user in the account
        :param str user_id: The user's identity id.
        :rtype: {LicensingSource}
        """
        route_values = {}
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        response = self._send(http_method='GET',
                              location_id='8cec75ea-044f-4245-ab0d-a82dafcc85ea',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('{LicensingSource}', self._unwrap_collection(response))

    def bulk_get_extensions_assigned_to_users(self, user_ids):
        """BulkGetExtensionsAssignedToUsers.
        [Preview API] Returns extensions that are currrently assigned to the users that are in the account
        :param [str] user_ids:
        :rtype: {[ExtensionSource]}
        """
        content = self._serialize.body(user_ids, '[str]')
        response = self._send(http_method='PUT',
                              location_id='1d42ddc2-3e7d-4daa-a0eb-e12c1dbd7c72',
                              version='4.1-preview.2',
                              content=content)
        return self._deserialize('{[ExtensionSource]}', self._unwrap_collection(response))

    def get_extension_license_data(self, extension_id):
        """GetExtensionLicenseData.
        [Preview API]
        :param str extension_id:
        :rtype: :class:`<ExtensionLicenseData> <licensing.v4_1.models.ExtensionLicenseData>`
        """
        route_values = {}
        if extension_id is not None:
            route_values['extensionId'] = self._serialize.url('extension_id', extension_id, 'str')
        response = self._send(http_method='GET',
                              location_id='004a420a-7bef-4b7f-8a50-22975d2067cc',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('ExtensionLicenseData', response)

    def register_extension_license(self, extension_license_data):
        """RegisterExtensionLicense.
        [Preview API]
        :param :class:`<ExtensionLicenseData> <licensing.v4_1.models.ExtensionLicenseData>` extension_license_data:
        :rtype: bool
        """
        content = self._serialize.body(extension_license_data, 'ExtensionLicenseData')
        response = self._send(http_method='POST',
                              location_id='004a420a-7bef-4b7f-8a50-22975d2067cc',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('bool', response)

    def compute_extension_rights(self, ids):
        """ComputeExtensionRights.
        [Preview API]
        :param [str] ids:
        :rtype: {bool}
        """
        content = self._serialize.body(ids, '[str]')
        response = self._send(http_method='POST',
                              location_id='5f1dbe21-f748-47c7-b5fd-3770c8bc2c08',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('{bool}', self._unwrap_collection(response))

    def get_extension_rights(self):
        """GetExtensionRights.
        [Preview API]
        :rtype: :class:`<ExtensionRightsResult> <licensing.v4_1.models.ExtensionRightsResult>`
        """
        response = self._send(http_method='GET',
                              location_id='5f1dbe21-f748-47c7-b5fd-3770c8bc2c08',
                              version='4.1-preview.1')
        return self._deserialize('ExtensionRightsResult', response)

    def get_msdn_presence(self):
        """GetMsdnPresence.
        [Preview API]
        """
        self._send(http_method='GET',
                   location_id='69522c3f-eecc-48d0-b333-f69ffb8fa6cc',
                   version='4.1-preview.1')

    def get_entitlements(self):
        """GetEntitlements.
        [Preview API]
        :rtype: [MsdnEntitlement]
        """
        response = self._send(http_method='GET',
                              location_id='1cc6137e-12d5-4d44-a4f2-765006c9e85d',
                              version='4.1-preview.1')
        return self._deserialize('[MsdnEntitlement]', self._unwrap_collection(response))

    def get_account_licenses_usage(self):
        """GetAccountLicensesUsage.
        [Preview API]
        :rtype: [AccountLicenseUsage]
        """
        response = self._send(http_method='GET',
                              location_id='d3266b87-d395-4e91-97a5-0215b81a0b7d',
                              version='4.1-preview.1')
        return self._deserialize('[AccountLicenseUsage]', self._unwrap_collection(response))

