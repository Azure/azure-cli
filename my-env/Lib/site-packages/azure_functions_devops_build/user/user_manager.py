# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
from msrest.exceptions import HttpOperationError
from . import models

class UserManager(object):
    """ Get details about a user

    Attributes:
        See BaseManager
    """

    def __init__(self, base_url='https://peprodscussu2.portalext.visualstudio.com', creds=None):
        """Inits UserManager as to be able to send the right requests"""
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(creds, self._config)
        #create the deserializer for the models
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)

        # create cache for two user type
        self._cache_aad_user = None
        self._cache_msa_user = None

    def is_msa_account(self):
        user_id_aad = self.get_user(msa=False).id
        user_id_msa = self.get_user(msa=True).id
        return user_id_aad != user_id_msa

    def get_user(self, msa=False):
        # Try to get from cache
        if msa is True and self._cache_msa_user is not None:
            return self._cache_msa_user
        if msa is False and self._cache_aad_user is not None:
            return self._cache_aad_user

        header_parameters = {}
        header_parameters['X-VSS-ForceMsaPassThrough'] = 'true' if msa else 'false'
        header_parameters['Accept'] = 'application/json'
        request = self._client.get('/_apis/AzureTfs/UserContext')
        response = self._client.send(request, header_parameters)

        # Handle Response
        deserialized = None
        if response.status_code // 100 != 2:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('User', response)

        # Write to cache
        if msa is True and self._cache_msa_user is None:
            self._cache_msa_user = deserialized
        if msa is False and self._cache_aad_user is None:
            self._cache_aad_user = deserialized

        return deserialized

    @property
    def aad_id(self):
        return self.get_user(msa=False).id

    @property
    def msa_id(self):
        return self.get_user(msa=True).id

    def close_connection(self):
        self._client.close()
