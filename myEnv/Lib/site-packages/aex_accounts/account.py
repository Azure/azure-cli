
from __future__ import print_function
from sys import stderr
from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
from msrest.exceptions import HttpOperationError
from .version import VERSION
from . import models

class AccountConfiguration(Configuration):

    def __init__(self, api_version, base_url=None):
        super(AccountConfiguration, self).__init__(base_url)
        self.add_user_agent('azurecli/vsts/{}'.format(VERSION))
        self.api_version = api_version

class Account(object):

    def __init__(self, api_version, base_url=None, creds=None):

        self.config = AccountConfiguration(api_version, base_url)
        self._client = ServiceClient(creds, self.config)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)
        self.api_version = api_version

    def create_account(self, collection_name, preferred_region):

        # Construct URL
        url = '/_apis/hostacquisition/collections'

        # Construct parameters
        query_parameters = {}
        query_parameters["api-version"] = self.api_version
        query_parameters["collectionName"] = collection_name
        query_parameters["preferredRegion"] = preferred_region

        # Construct and send request
        request = self._client.post(url, query_parameters)
        response = self._client.send(request)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            print("POST", request.url, file=stderr)
            print("response:", response.status_code, file=stderr)
            print(response.text, file=stderr)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Collection', response)

        return deserialized

    def regions(self):

        # Construct URL
        url = '/_apis/hostacquisition/regions'

        # Construct and send request
        request = self._client.get(url)
        response = self._client.send(request)

        # Handle Response
        deserialized = None
        if response.status_code not in [200]:
            print("GET", request.url, file=stderr)
            print("response:", response.status_code, file=stderr)
            print(response.text, file=stderr)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Regions', response)

        return deserialized