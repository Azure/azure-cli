#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
import os
import sys
import copy
import requests

from abc import ABCMeta
from azure.common import (
    AzureException,
)
from ._constants import (
    _USER_AGENT_STRING,
    _SOCKET_TIMEOUT
)
from ._http import HTTPError
from ._http.httpclient import _HTTPClient
from ._serialization import (
    _storage_error_handler,
    _update_request,
)
from ._error import (
    _ERROR_STORAGE_MISSING_INFO,
)

class StorageClient(object):

    '''
    This is the base class for service objects. Service objects are used to do 
    all requests to Storage. This class cannot be instantiated directly.
    '''

    __metaclass__ = ABCMeta

    def __init__(self, connection_params):
        '''
        :param obj connection_params: The parameters to use to construct the client.
        '''
        self.account_name = connection_params.account_name
        self.account_key = connection_params.account_key
        self.sas_token = connection_params.sas_token

        self.protocol = connection_params.protocol
        self.primary_endpoint = connection_params.primary_endpoint
        self.secondary_endpoint = connection_params.secondary_endpoint

        self.request_session = connection_params.request_session

        self._httpclient = _HTTPClient(
            service_instance=self,
            protocol=self.protocol,
            request_session=connection_params.request_session or requests.Session(),
            user_agent=_USER_AGENT_STRING,
            timeout=_SOCKET_TIMEOUT,
        )
        self._filter = self._perform_request_worker

    def with_filter(self, filter):
        '''
        Returns a new service which will process requests with the specified
        filter. Filtering operations can include logging, automatic retrying,
        etc... The filter is a lambda which receives the HTTPRequest and
        another lambda. The filter can perform any pre-processing on the
        request, pass it off to the next lambda, and then perform any
        post-processing on the response.

        :param function(request) filter: A filter function.
        :return: A new service using the specified filter.
        :rtype: a subclass of :class:`StorageClient`
        '''
        res = copy.deepcopy(self)
        old_filter = self._filter

        def new_filter(request):
            return filter(request, old_filter)

        res._filter = new_filter
        return res

    def set_proxy(self, host, port, user=None, password=None):
        '''
        Sets the proxy server host and port for the HTTP CONNECT Tunnelling.

        :param str host: Address of the proxy. Ex: '192.168.0.100'
        :param int port: Port of the proxy. Ex: 6000
        :param str user: User for proxy authorization.
        :param str password: Password for proxy authorization.
        '''
        self._httpclient.set_proxy(host, port, user, password)

    def _get_host(self):
        return self.primary_endpoint

    def _perform_request_worker(self, request):
        _update_request(request)
        self.authentication.sign_request(request)
        return self._httpclient.perform_request(request)

    def _perform_request(self, request, encoding='utf-8'):
        '''
        Sends the request and return response. Catches HTTPError and hands it
        to error handler
        '''
        try:
            resp = self._filter(request)

            if sys.version_info >= (3,) and isinstance(resp, bytes) and \
                encoding:
                resp = resp.decode(encoding)

        # Parse and wrap HTTP errors in AzureHttpError which inherits from AzureException
        except HTTPError as ex:
            _storage_error_handler(ex)

        # Wrap all other exceptions as AzureExceptions to ease exception handling code
        except Exception as ex:
            if sys.version_info >= (3,):
                # Automatic chaining in Python 3 means we keep the trace
                raise AzureException
            else:
                # There isn't a good solution in 2 for keeping the stack trace 
                # in general, or that will not result in an error in 3
                # However, we can keep the previous error type and message
                # TODO: In the future we will log the trace
                raise AzureException('{}: {}'.format(ex.__class__.__name__, ex.args[0]))

        return resp
