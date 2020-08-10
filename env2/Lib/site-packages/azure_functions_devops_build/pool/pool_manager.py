# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import logging

from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
from msrest.exceptions import HttpOperationError

from ..user.user_manager import UserManager
from ..base.base_manager import BaseManager
from . import models

class PoolManager(BaseManager):
    """ Manage DevOps Pools

    Attributes:
        See BaseManager
    """

    def __init__(self, base_url='https://{}.visualstudio.com', creds=None, organization_name="", project_name=""):
        """Inits PoolManager"""
        super(PoolManager, self).__init__(creds, organization_name=organization_name, project_name=project_name)
        base_url = base_url.format(organization_name)
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(creds, self._config)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)
        self._user_mgr = UserManager(creds=self._creds)

    def list_pools(self):
        """List what pools this project has"""
        project = self._get_project_by_name(self._project_name)

        # Construct URL
        url = "/" + project.id + "/_apis/distributedtask/queues?actionFilter=16"

        #construct header parameters
        header_paramters = {}
        if self._user_mgr.is_msa_account():
            header_paramters['X-VSS-ForceMsaPassThrough'] = 'true'
        header_paramters['Accept'] = 'application/json'

        # Construct and send request
        request = self._client.get(url, headers=header_paramters)
        response = self._client.send(request)

        # Handle Response
        deserialized = None
        if response.status_code // 100 != 2:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Pools', response)

        return deserialized

    def close_connection(self):
        self._client.close()
