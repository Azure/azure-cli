# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import logging
from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
from msrest.exceptions import HttpOperationError

from ..user.user_manager import UserManager
from . import models


class OrganizationManager():
    """ Manage DevOps organizations

    Create or list existing organizations

    Attributes:
        config: url configuration
        client: authentication client
        dserialize: deserializer to process http responses into python classes
    """

    def __init__(self, base_url='https://app.vssps.visualstudio.com', creds=None,
                 create_organization_url='https://app.vsaex.visualstudio.com'):
        """Inits OrganizationManager"""
        self._creds = creds
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(creds, self._config)
        # need to make a secondary client for the creating organization as it uses a different base url
        self._create_organization_config = Configuration(base_url=create_organization_url)
        self._create_organization_client = ServiceClient(creds, self._create_organization_config)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)

    def validate_organization_name(self, organization_name):
        """Validate an organization name by checking it does not already exist and that it fits name restrictions"""
        if re.search("[^0-9A-Za-z-]", organization_name):
            return models.ValidateAccountName(valid=False, message="""The name supplied contains forbidden characters.
                                                                      Only alphanumeric characters and dashes are allowed.
                                                                      Please try another organization name.""")
        # construct url
        url = '/_AzureSpsAccount/ValidateAccountName'

        # construct query parameters
        query_paramters = {}
        query_paramters['accountName'] = organization_name

        # construct header parameters
        header_paramters = {}
        header_paramters['Accept'] = 'application/json'

        request = self._client.get(url, params=query_paramters)
        response = self._client.send(request, headers=header_paramters)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('ValidateAccountName', response)

        return deserialized

    def list_organizations(self):
        """List what organizations this user is part of"""

        user_manager = UserManager(creds=self._creds)

        user_id_aad = user_manager.get_user_id(msa=False)
        user_id_msa = user_manager.get_user_id(msa=True)

        if user_id_aad.id == user_id_msa.id:
            # Only need to do the one request as ids are the same
            organizations = self._list_organizations_request(user_id_aad.id)
        else:
            def uniq(lst):
                last = object()
                for item in lst:
                    if item == last:
                        continue
                    yield item
                    last = item
            # Need to do a request for each of the ids and then combine them
            organizations_aad = self._list_organizations_request(user_id_aad.id, msa=False)
            organizations_msa = self._list_organizations_request(user_id_msa.id, msa=True)
            organizations = organizations_aad
            # Now we just want to take the set of these two lists!
            organizations.value = list(uniq(organizations_aad.value + organizations_msa.value))
            organizations.count = len(organizations.value)

        return organizations

    def _list_organizations_request(self, member_id, msa=False):
        url = '/_apis/Commerce/Subscription'

        query_paramters = {}
        query_paramters['memberId'] = member_id
        query_paramters['includeMSAAccounts'] = True
        query_paramters['queryOnlyOwnerAccounts'] = True
        query_paramters['inlcudeDisabledAccounts'] = False
        query_paramters['providerNamespaceId'] = 'VisualStudioOnline'

        # construct header parameters
        header_parameters = {}
        if msa:
            header_parameters['X-VSS-ForceMsaPassThrough'] = 'true'
        header_parameters['Accept'] = 'application/json'

        request = self._client.get(url, params=query_paramters)
        response = self._client.send(request, headers=header_parameters)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Organizations', response)

        return deserialized

    def create_organization(self, region_code, organization_name):
        """Create a new organization for user"""
        url = '/_apis/HostAcquisition/collections'

        # construct query parameters
        query_paramters = {}
        query_paramters['collectionName'] = organization_name
        query_paramters['preferredRegion'] = region_code
        query_paramters['api-version'] = '4.0-preview.1'

        # construct header parameters
        header_paramters = {}
        header_paramters['Accept'] = 'application/json'
        header_paramters['Content-Type'] = 'application/json'

        # construct the payload
        payload = {}
        payload['VisualStudio.Services.HostResolution.UseCodexDomainForHostCreation'] = 'true'

        request = self._create_organization_client.post(url=url, params=query_paramters, content=payload)
        response = self._create_organization_client.send(request, headers=header_paramters)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('NewOrganization', response)

        return deserialized

    def list_regions(self):
        """List what regions organizations can exist in"""

        # Construct URL
        url = '/_apis/commerce/regions'

        # construct header parameters
        header_paramters = {}
        header_paramters['Accept'] = 'application/json'

        # Construct and send request
        request = self._client.get(url, headers=header_paramters)
        response = self._client.send(request)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Regions', response)

        return deserialized

    def close_connection(self):
        """Close the sessions"""
        self._client.close()
        self._create_organization_client.close()
