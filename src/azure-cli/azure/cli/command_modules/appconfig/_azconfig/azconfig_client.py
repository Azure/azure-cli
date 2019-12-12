# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import requests
import azure.cli.command_modules.appconfig._azconfig.keyvalue_iterable as iterable
import azure.cli.command_modules.appconfig._azconfig.exceptions as exceptions
import azure.cli.command_modules.appconfig._azconfig.constants as constants
import azure.cli.command_modules.appconfig._azconfig.utils as utils
import azure.cli.command_modules.appconfig._azconfig.models as models
import azure.cli.command_modules.appconfig._azconfig.mapper as mapper
import azure.cli.command_modules.appconfig._azconfig.request_message as request_message
import azure.cli.command_modules.appconfig._azconfig.request_handler as handler


class AzconfigClient(object):
    """Represents an azconfig client.

    Provides a client-side logical representation of the Azure config service.
    This client is used to configure and execute requests against the
    service.

    The service client encapsulates the endpoint and credentials used to access
    the Azure config service.
    """

    def __init__(self, connection_string, client_options=None):
        """
        :param string connection_params:
            Contains 'endpoint', 'id' and 'secret', where id and secret are credentials
            used to create the client.
        :param ClientOptions client_options:
            Optional parameter to customize AzconfigClient

        """
        self.connection_string = connection_string
        self._request_session = requests.Session()

        self._client_options = models.ClientOptions(
        ) if client_options is None else client_options

        self._default_headers = {
            constants.HttpHeaders.UserAgent: self._client_options.user_agent
        }

        self._request_handler = handler.RequestHandler(
            connection_string, self._client_options)

    def add_keyvalue(self, keyvalue, modify_options=None):
        """ Adds a new key-value to a configuration store.

        :param KeyValue keyvalue:
            The key-value to add.
        :param dict custom_headers:
            Headers that will be added to the request
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The key-value that was added to the configuration store.
        :rtype:
            KeyValue

        :raises ValueError: If the keyvalue entry alreay exists.

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)
        body_content = {
            "content_type": keyvalue.content_type,
            "value": keyvalue.value,
            "tags": keyvalue.tags
        }

        return self.__write_key(key,
                                label,
                                body_content,
                                modify_options,
                                if_match_etag=None,
                                if_none_match_etag='*')

    def set_keyvalue(self, keyvalue, modify_options=None):
        """ Sets a key-value's properties within a configuration store.
        If the key-value does not exist it will be created.

        :param KeyValue keyvalue:
            The key-value to set.
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The key-value that was set in the configuration store.
        :rtype:
            KeyValue

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)
        body_content = {
            "content_type": keyvalue.content_type,
            "value": keyvalue.value,
            "tags": keyvalue.tags
        }
        return self.__write_key(key,
                                label,
                                body_content,
                                modify_options)

    def update_keyvalue(self, keyvalue, modify_options=None):
        """ Updates a key-value that was retrieved from a configuration store.
        The ETag property is used to ensure that no external changes to the key-value have
        occurred in the configuration store since the key-value was retrieved.

        :param KeyValue keyvalue:
            The key-value to update.
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The updated key-value.
        :rtype:
            KeyValue

        :raises ValueError: If the keyvalue entry has been modified and etag mismatches.

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        if keyvalue.etag is None:
            raise ValueError("Etag of the keyvalue cannot be null")

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)
        body_content = {
            "content_type": keyvalue.content_type,
            "value": keyvalue.value,
            "tags": keyvalue.tags
        }
        return self.__write_key(key,
                                label,
                                body_content,
                                modify_options,
                                keyvalue.etag)

    def delete_keyvalue_by_key_label(self, key, label=None, modify_options=None):
        """ Deletes a key-value from a configuration store.

        :param str key:
            The key of the key-value that should be deleted.
        :param str label:
            The label of the key-value that should be deleted.
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The deleted key-value if found, otherwise null.
        :rtype:
            KeyValue

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        key, label = utils.unescape_encode_key_and_label(key, label)
        query_url = '/kv/{}?label={}'.format(key, '' if label is None else label)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(modify_options)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Delete,
                                                custom_headers=custom_headers,
                                                datetime_=None,
                                                if_match_etag=None)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Delete, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())
        if response.status_code == constants.StatusCodes.NO_CONTENT:
            return None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def delete_keyvalue(self, keyvalue, modify_options=None):
        """ Deletes a key-value from a configuration store.
        The ETag property is used to ensure that no external changes to the key-value have occurred in the configuration store since the key-value was retrieved.

        :param str keyvalue:
            The key-value to delete.
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The deleted key-value.
        :rtype:
            KeyValue

        :raises ValueError: If the key-value entry has been modified and etag mismatches.

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        if keyvalue.etag is None:
            raise ValueError("Etag of the keyvalue cannot be null")

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)
        query_url = '/kv/{}?label={}'.format(key, '' if label is None else label)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(modify_options)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Delete,
                                                custom_headers=custom_headers,
                                                datetime_=None,
                                                if_match_etag=keyvalue.etag)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Delete, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())
        if response.status_code == constants.StatusCodes.PRECONDITION_FAILED:
            raise ValueError('The keyvalue entry has been modified.')

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def get_keyvalue(self, key, query_options=None):
        """Retrieves a key-value with the specified key, taking into account the constraints of the key-value query options.

        :param str key:
            The key of the key-value to retrieved.
        :param QueryKeyValueOptions query_options:
            Parameters used to modify which key-value is retrieved.

        :return:
            The key-value if found, otherwise null
        :rtype:
            KeyValue
        """

        if query_options is None:
            query_options = models.QueryKeyValueOptions()

        return self.__query_key(key, query_options)

    def get_keyvalues(self, query_options=None):
        """Returns an iterable object which allows the caller to iterate and retrieve key-values.

        :param QueryKeyValueCollectionOptions query_options:
            Parameters used to modify the set of key-values that are retrieved.

        :return:
            An iterable of key-values if found, otherwise an empty one                                                                                                                                                                                                                                                                                                                                                                                                                                                                     .
        :rtype: KeyValueIterable

        """
        if query_options is None:
            query_options = models.QueryKeyValueCollectionOptions

        return iterable.KeyValueIterable(self, query_options, self.__query_keys)

    def read_keyvalue_revisions(self, query_options=None):
        """Returns an iterable object which allows the caller to asynchronously iterate and retrieve revisions.

        :param QueryKeyValueCollectionOptions query_options:
            Parameters used to modify the set of revisions that are retrieved.

        :return:
             An iterable of key-value revisions if found, otherwise an empty one
        :rtype: KeyValueIterable

        """
        if query_options is None:
            query_options = models.QueryKeyValueCollectionOptions

        return iterable.KeyValueIterable(self, query_options, self.__list_revision)

    def lock_keyvalue(self, keyvalue, modify_options=None):
        """Locks a key-value within a configuration store.

        :param KeyValue keyvalue:
            The key-value to be locked..
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The locked key-value if its ETag matches the ETag in the configuration store, otherwise null.
        :rtype: KeyValue

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)

        query_url = '/locks/{}'.format(key)
        query_url += '?label={}'.format('' if label is None else label)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(modify_options)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Put,
                                                custom_headers=custom_headers,
                                                datetime_=None,
                                                if_match_etag=keyvalue.etag)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Put, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())
        if response.status_code == constants.StatusCodes.NO_CONTENT:
            return None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def unlock_keyvalue(self, keyvalue, modify_options=None):
        """Unlocks a key-value within a configuration store.

        :param KeyValue keyvalue:
            The key-value to be unlocked.
        :param ModifyKeyValueOptions modify_options:
            Optional parameter to set keyvalue modification options

        :return:
            The unlocked key-value if its ETag matches the ETag in the configuration store, otherwise null.
        :rtype: KeyValue

        """
        if modify_options is None:
            modify_options = models.ModifyKeyValueOptions()

        key, label = utils.unescape_encode_key_and_label(keyvalue.key, keyvalue.label)

        query_url = '/locks/{}'.format(key)
        query_url += '?label={}'.format('' if label is None else label)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(modify_options)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Delete,
                                                custom_headers=custom_headers,
                                                datetime_=None,
                                                if_match_etag=keyvalue.etag)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Delete, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())
        if response.status_code == constants.StatusCodes.NO_CONTENT:
            return None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    # pylint: disable=too-many-arguments

    def __write_key(self,
                    key,
                    label,
                    body_content,
                    modify_options,
                    if_match_etag=None,
                    if_none_match_etag=None):
        query_url = '/kv/{}?label={}'.format(key, '' if label is None else label)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(modify_options)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Put,
                                                custom_headers=custom_headers,
                                                datetime_=None,
                                                if_match_etag=if_match_etag,
                                                if_none_match_etag=if_none_match_etag)

        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Put, headers, url, json.dumps(body_content)), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def __list_revision(self, query_option, continuation_link):
        key, label = utils.unescape_encode_key_and_label(query_option.key_filter, query_option.label_filter)
        query_datetime = query_option.query_datetime
        query_fields = self.__construct_query_fields_to_string(
            query_option.fields)

        if continuation_link is None:
            query_url = '/revisions?key={}'.format('*' if key is None else key)
            query_url += '&label={}'.format('*'if label is None else label)
            query_url += '&fields={}'.format(query_fields)
            query_url = self.__append_api_version(query_url)
        else:
            query_url = self.__parse_link_header(continuation_link)
            if query_url is None:
                return [], None

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(query_option)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Get,
                                                custom_headers=custom_headers,
                                                datetime_=query_datetime)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Get, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            if constants.HttpHeaders.Link in response.headers:
                return mapper.map_json_to_keyvalues(response.json()['items']), response.headers[constants.HttpHeaders.Link]
            return mapper.map_json_to_keyvalues(response.json()['items']), None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def __query_key(self, key, query_kv_option):
        key, label = utils.unescape_encode_key_and_label(key, query_kv_option.label)
        fields = self.__construct_query_fields_to_string(
            query_kv_option.fields)

        query_url = '/kv/{}?label={}'.format(key,
                                             label if label is not None else '')
        query_url += '&fields={}'.format('*' if fields is None else fields)
        query_url = self.__append_api_version(query_url)

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(query_kv_option)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Get,
                                                custom_headers=custom_headers,
                                                datetime_=None if query_kv_option is None else query_kv_option.query_datetime)

        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Get, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            return mapper.map_json_to_keyvalue(response.json())
        if response.status_code == constants.StatusCodes.NOT_FOUND:
            return None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    def __query_keys(self, query_kv_collection_option, continuation_link):
        key, label = utils.unescape_encode_key_and_label(query_kv_collection_option.key_filter, query_kv_collection_option.label_filter)

        query_datetime = query_kv_collection_option.query_datetime
        query_fields = self.__construct_query_fields_to_string(
            query_kv_collection_option.fields)

        if continuation_link is None:
            query_url = '/kv?key={}'.format('*' if key is None else key)
            query_url += '&label={}'.format('*' if label is None else label)
            query_url += '&fields={}'.format('*' if query_fields is None else query_fields)
            query_url = self.__append_api_version(query_url)
        else:
            query_url = self.__parse_link_header(continuation_link)
            if query_url is None:
                return [], None

        endpoint = utils.get_endpoint_from_connection_string(
            self.connection_string)
        url = 'https://{}{}'.format(endpoint, query_url)

        custom_headers = self.__configure_request_ids(
            query_kv_collection_option)
        custom_headers.update(self._default_headers)

        headers = utils.generate_request_header(method=constants.HttpMethods.Get,
                                                custom_headers=custom_headers,
                                                datetime_=query_datetime)
        response = self._request_handler.execute(request_message.RequestMessage(
            constants.HttpMethods.Get, headers, url, ''), self._request_session)

        if response.status_code == constants.StatusCodes.OK:
            if constants.HttpHeaders.Link in response.headers:
                return mapper.map_json_to_keyvalues(response.json()['items']), response.headers[constants.HttpHeaders.Link]

            return mapper.map_json_to_keyvalues(response.json()['items']), None

        raise exceptions.HTTPException(response.status_code, response.reason,
                                       response.headers, response.content)

    @staticmethod
    def __parse_link_header(link_header):
        # link header looks like "</kv?after=last>; rel="next", </kv?before=first>; rel="before""
        uri_start = 0
        for index, char in enumerate(link_header):
            if char == '<':
                uri_start = index
            elif char == '>':
                if str(link_header[index + 3: index + 13]) == '''rel="next"''':
                    return str(link_header[uri_start + 1: index])
        return None

    @staticmethod
    def __construct_query_fields_to_string(query_fields):
        query_fields_string = ''
        if query_fields is not None:
            for field in query_fields:
                if field == models.QueryFields.ALL:
                    query_fields = '*'
                    break
                query_fields_string += field.name.lower() + ","
        return query_fields_string[:-1]

    @staticmethod
    def __configure_request_ids(request_options):
        custom_headers = {}

        custom_headers[constants.HttpHeaders.ClientRequestId] = request_options.client_request_id
        custom_headers[constants.HttpHeaders.CorrelationRequestId] = request_options.correlation_request_id

        return custom_headers

    @staticmethod
    def __append_api_version(url):
        api_version = "&api-version=" if '?' in url else "?api-version="
        return url + api_version + constants.Versions.ApiVersion
