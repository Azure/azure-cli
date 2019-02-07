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
        # create the deserializer for the models
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)

    def get_user_id(self, msa=False):
        """Get the user id"""

        header_parameters = {}
        if msa:
            header_parameters['X-VSS-ForceMsaPassThrough'] = 'true'
        header_parameters['Accept'] = 'application/json'
        request = self._client.get('/_apis/AzureTfs/UserContext')
        response = self._client.send(request, header_parameters)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('User', response)

        return deserialized

    def close_connection(self):
        self._client.close()
