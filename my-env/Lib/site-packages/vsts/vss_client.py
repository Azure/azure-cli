# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import logging
import os
import re
import uuid

from msrest import Deserializer, Serializer
from msrest.exceptions import DeserializationError, SerializationError
from msrest.universal_http import ClientRequest
from msrest.service_client import ServiceClient
from .exceptions import VstsAuthenticationError, VstsClientRequestError, VstsServiceError
from .vss_client_configuration import VssClientConfiguration
from . import models
from ._file_cache import OPTIONS_CACHE as OPTIONS_FILE_CACHE


logger = logging.getLogger(__name__)


class VssClient(object):
    """VssClient.
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        self.config = VssClientConfiguration(base_url)
        self.config.credentials = creds
        self._client = ServiceClient(creds, config=self.config)
        _base_client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._base_deserialize = Deserializer(_base_client_models)
        self._base_serialize = Serializer(_base_client_models)
        self._all_host_types_locations = None
        self._locations = None
        self._suppress_fedauth_redirect = True
        self._force_msa_pass_through = True
        self.normalized_url = VssClient._normalize_url(base_url)

    def add_user_agent(self, user_agent):
        if user_agent is not None:
            self.config.add_user_agent(user_agent)

    def _send_request(self, request, headers=None, content=None, **operation_config):
        """Prepare and send request object according to configuration.
        :param ClientRequest request: The request object to be sent.
        :param dict headers: Any headers to add to the request.
        :param content: Any body data to add to the request.
        :param config: Any specific config overrides
        """
        if TRACE_ENV_VAR in os.environ and os.environ[TRACE_ENV_VAR] == 'true':
            print(request.method + ' ' + request.url)
        logger.debug('%s %s', request.method, request.url)
        logger.debug('Request content: %s', content)
        response = self._client.send(request=request, headers=headers,
                                     content=content, **operation_config)
        logger.debug('Response content: %s', response.content)
        if response.status_code < 200 or response.status_code >= 300:
            self._handle_error(request, response)
        return response

    def _send(self, http_method, location_id, version, route_values=None,
              query_parameters=None, content=None, media_type='application/json', accept_media_type='application/json'):
        request = self._create_request_message(http_method=http_method,
                                               location_id=location_id,
                                               route_values=route_values,
                                               query_parameters=query_parameters)
        negotiated_version = self._negotiate_request_version(
            self._get_resource_location(location_id),
            version)

        if version != negotiated_version:
            logger.info("Negotiated api version from '%s' down to '%s'. This means the client is newer than the server.",
                        version,
                        negotiated_version)
        else:
            logger.debug("Api version '%s'", negotiated_version)

        # Construct headers
        headers = {'Content-Type': media_type + '; charset=utf-8',
                   'Accept': accept_media_type + ';api-version=' + negotiated_version}
        if self.config.additional_headers is not None:
            for key in self.config.additional_headers:
                headers[key] = self.config.additional_headers[key]
        if self._suppress_fedauth_redirect:
            headers['X-TFS-FedAuthRedirect'] = 'Suppress'
        if self._force_msa_pass_through:
            headers['X-VSS-ForceMsaPassThrough'] = 'true'
        if VssClient._session_header_key in VssClient._session_data and VssClient._session_header_key not in headers:
            headers[VssClient._session_header_key] = VssClient._session_data[VssClient._session_header_key]
        response = self._send_request(request=request, headers=headers, content=content)
        if VssClient._session_header_key in response.headers:
            VssClient._session_data[VssClient._session_header_key] = response.headers[VssClient._session_header_key]
        return response

    def _unwrap_collection(self, response):
        if response.headers.get("transfer-encoding") == 'chunked':
            wrapper = self._base_deserialize.deserialize_data(response.json(), 'VssJsonCollectionWrapper')
        else:
            wrapper = self._base_deserialize('VssJsonCollectionWrapper', response)
        collection = wrapper.value
        return collection

    def _create_request_message(self, http_method, location_id, route_values=None,
                                query_parameters=None):
        location = self._get_resource_location(location_id)
        if location is None:
            raise ValueError('API resource location ' + location_id + ' is not registered on '
                             + self.config.base_url + '.')
        if route_values is None:
            route_values = {}
        route_values['area'] = location.area
        route_values['resource'] = location.resource_name
        route_template = self._remove_optional_route_parameters(location.route_template,
                                                                route_values)
        logger.debug('Route template: %s', location.route_template)
        url = self._client.format_url(route_template, **route_values)
        request = ClientRequest(method=http_method, url=self._client.format_url(url))
        if query_parameters:
            request.format_parameters(query_parameters)
        return request

    @staticmethod
    def _remove_optional_route_parameters(route_template, route_values):
        new_template = ''
        route_template = route_template.replace('{*', '{')
        for path_segment in route_template.split('/'):
            if (len(path_segment) <= 2 or not path_segment[0] == '{'
                    or not path_segment[len(path_segment) - 1] == '}'
                    or path_segment[1:len(path_segment) - 1] in route_values):
                new_template = new_template + '/' + path_segment
        return new_template

    def _get_resource_location(self, location_id):
        if self.config.base_url not in VssClient._locations_cache:
            VssClient._locations_cache[self.config.base_url] = self._get_resource_locations(all_host_types=False)
        for location in VssClient._locations_cache[self.config.base_url]:
            if location.id == location_id:
                return location

    def _get_resource_locations(self, all_host_types):
        # Check local client's cached Options first
        if all_host_types:
            if self._all_host_types_locations is not None:
                return self._all_host_types_locations
        elif self._locations is not None:
            return self._locations

        # Next check for options cached on disk
        if not all_host_types and OPTIONS_FILE_CACHE[self.normalized_url]:
            try:
                logger.debug('File cache hit for options on: %s', self.normalized_url)
                self._locations = self._base_deserialize.deserialize_data(OPTIONS_FILE_CACHE[self.normalized_url],
                                                                          '[ApiResourceLocation]')
                return self._locations
            except DeserializationError as ex:
                logger.debug(ex, exc_info=True)
        else:
            logger.debug('File cache miss for options on: %s', self.normalized_url)

        # Last resort, make the call to the server
        options_uri = self._combine_url(self.config.base_url, '_apis')
        request = ClientRequest(method='OPTIONS', url=self._client.format_url(options_uri))
        if all_host_types:
            query_parameters = {'allHostTypes': True}
            request.format_parameters(query_parameters)
        headers = {'Accept': 'application/json'}
        if self._suppress_fedauth_redirect:
            headers['X-TFS-FedAuthRedirect'] = 'Suppress'
        if self._force_msa_pass_through:
            headers['X-VSS-ForceMsaPassThrough'] = 'true'
        response = self._send_request(request, headers=headers)
        wrapper = self._base_deserialize('VssJsonCollectionWrapper', response)
        if wrapper is None:
            raise VstsClientRequestError("Failed to retrieve resource locations from: {}".format(options_uri))
        collection = wrapper.value
        returned_locations = self._base_deserialize('[ApiResourceLocation]',
                                                    collection)
        if all_host_types:
            self._all_host_types_locations = returned_locations
        else:
            self._locations = returned_locations
            try:
                OPTIONS_FILE_CACHE[self.normalized_url] = wrapper.value
            except SerializationError as ex:
                logger.debug(ex, exc_info=True)
        return returned_locations

    @staticmethod
    def _negotiate_request_version(location, version):
        if location is None or version is None:
            return version
        pattern = r'(\d+(\.\d)?)(-preview(.(\d+))?)?'
        match = re.match(pattern, version)
        requested_api_version = match.group(1)
        if requested_api_version is not None:
            requested_api_version = float(requested_api_version)
        if location.min_version > requested_api_version:
            # Client is older than the server. The server no longer supports this
            # resource (deprecated).
            return
        elif location.max_version < requested_api_version:
            # Client is newer than the server. Negotiate down to the latest version
            # on the server
            negotiated_version = str(location.max_version)
            if float(location.released_version) < location.max_version:
                negotiated_version += '-preview'
            return negotiated_version
        else:
            # We can send at the requested api version. Make sure the resource version
            # is not bigger than what the server supports
            negotiated_version = str(requested_api_version)
            is_preview = match.group(3) is not None
            if is_preview:
                negotiated_version += '-preview'
                if match.group(5) is not None:
                    if location.resource_version < int(match.group(5)):
                        negotiated_version += '.' + str(location.resource_version)
                    else:
                        negotiated_version += '.' + match.group(5)
            return negotiated_version

    @staticmethod
    def _combine_url(part1, part2):
        return part1.rstrip('/') + '/' + part2.strip('/')

    def _handle_error(self, request, response):
        content_type = response.headers.get('Content-Type')
        error_message = ''
        if content_type is None or content_type.find('text/plain') < 0:
            try:
                wrapped_exception = self._base_deserialize('WrappedException', response)
                if wrapped_exception is not None and wrapped_exception.message is not None:
                    raise VstsServiceError(wrapped_exception)
                else:
                    # System exceptions from controllers are not returning wrapped exceptions.
                    # Following code is to handle this unusual exception json case.
                    # TODO: dig into this.
                    collection_wrapper = self._base_deserialize('VssJsonCollectionWrapper', response)
                    if collection_wrapper is not None and collection_wrapper.value is not None:
                        wrapped_exception = self._base_deserialize('ImproperException', collection_wrapper.value)
                        if wrapped_exception is not None and wrapped_exception.message is not None:
                            raise VstsClientRequestError(wrapped_exception.message)
                # if we get here we still have not raised an exception, try to deserialize as a System Exception
                system_exception = self._base_deserialize('SystemException', response)
                if system_exception is not None and system_exception.message is not None:
                    raise VstsClientRequestError(system_exception.message)
            except DeserializationError:
                pass
        elif response.content is not None:
            error_message = response.content.decode("utf-8") + '  '
        if response.status_code == 401:
            full_message_format = '{error_message}The requested resource requires user authentication: {url}'
            raise VstsAuthenticationError(full_message_format.format(error_message=error_message,
                                                                     url=request.url))
        else:
            full_message_format = '{error_message}Operation returned an invalid status code of {status_code}.'
            raise VstsClientRequestError(full_message_format.format(error_message=error_message,
                                                                    status_code=response.status_code))

    @staticmethod
    def _normalize_url(url):
        return url.rstrip('/').lower()

    _locations_cache = {}
    _session_header_key = 'X-TFS-Session'
    _session_data = {_session_header_key: str(uuid.uuid4())}


TRACE_ENV_VAR = 'vsts_python_print_urls'
