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
from azure.common import (
    AzureConflictHttpError,
    AzureHttpError,
)
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
)
from .._error import (
    _dont_fail_not_exist,
    _dont_fail_on_exist,
    _validate_not_none,
    _ERROR_CONFLICT,
    _ERROR_STORAGE_MISSING_INFO,
    _validate_access_policies,
    _validate_encryption_required,
    _validate_decryption_required,
)
from .._serialization import (
    _get_request_body,
    _add_metadata_headers,
)
from .._common_conversion import (
    _int_to_str,
    _to_str,
)
from .._http import (
    HTTPRequest,
)
from ..models import (
    Services,
    ListGenerator,
    _OperationContext,
)
from .models import (
    QueueMessageFormat,
)
from .._auth import (
    _StorageSASAuthentication,
    _StorageSharedKeyAuthentication,
)
from .._connection import _ServiceParameters
from .._serialization import (
    _convert_signed_identifiers_to_xml,
    _convert_service_properties_to_xml,
)
from .._deserialization import (
    _convert_xml_to_service_properties,
    _convert_xml_to_signed_identifiers,
    _convert_xml_to_service_stats,
)
from ._serialization import (
    _convert_queue_message_xml,
    _get_path,
)
from ._deserialization import (
    _convert_xml_to_queues,
    _convert_xml_to_queue_messages,
    _parse_queue_message_from_headers,
    _parse_metadata_and_message_count,
)
from ..sharedaccesssignature import (
    SharedAccessSignature,
)
from ..storageclient import StorageClient


_HTTP_RESPONSE_NO_CONTENT = 204

class QueueService(StorageClient):

    '''
    This is the main class managing queue resources.

    The Queue service stores messages. A queue can contain an unlimited number of 
    messages, each of which can be up to 64KB in size. Messages are generally added 
    to the end of the queue and retrieved from the front of the queue, although 
    first in, first out (FIFO) behavior is not guaranteed.

    :ivar function(data) encode_function: 
        A function used to encode queue messages. Takes as 
        a parameter the data passed to the put_message API and returns the encoded 
        message. Defaults to take text and xml encode, but bytes and other 
        encodings can be used. For example, base64 may be preferable for developing 
        across multiple Azure Storage libraries in different languages. See the 
        :class:`~azure.storage.queue.models.QueueMessageFormat` for xml, base64 and 
        no encoding methods as well as binary equivalents.
    :ivar function(data) decode_function: 
        A function used to encode decode messages. Takes as 
        a parameter the data returned by the get_messages and peek_messages APIs and 
        returns the decoded message. Defaults to return text and xml decode, but 
        bytes and other decodings can be used. For example, base64 may be preferable 
        for developing across multiple Azure Storage libraries in different languages. 
        See the :class:`~azure.storage.queue.models.QueueMessageFormat` for xml, base64 
        and no decoding methods as well as binary equivalents.
    :ivar object key_encryption_key:
        The key-encryption-key optionally provided by the user. If provided, will be used to
        encrypt/decrypt in supported methods.
        For methods requiring decryption, either the key_encryption_key OR the resolver must be provided.
        If both are provided, the resolver will take precedence.
        Must implement the following methods for APIs requiring encryption:
        wrap_key(key)--wraps the specified key (bytes) using an algorithm of the user's choice. Returns the encrypted key as bytes.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
        Must implement the following methods for APIs requiring decryption:
        unwrap_key(key, algorithm)--returns the unwrapped form of the specified symmetric key using the string-specified algorithm.
        get_kid()--returns a string key id for this key-encryption-key.
    :ivar function key_resolver_function(kid):
        A function to resolve keys optionally provided by the user. If provided, will be used to decrypt in supported methods.
        For methods requiring decryption, either the key_encryption_key OR
        the resolver must be provided. If both are provided, the resolver will take precedence.
        It uses the kid string to return a key-encryption-key implementing the interface defined above.
    :ivar bool require_encryption:
        A flag that may be set to ensure that all messages successfully uploaded to the queue and all those downloaded and
        successfully read from the queue are/were encrypted while on the server. If this flag is set, all required 
        parameters for encryption/decryption must be provided. See the above comments on the key_encryption_key and resolver.
    '''

    def __init__(self, account_name=None, account_key=None, sas_token=None, 
                 is_emulated=False, protocol=DEFAULT_PROTOCOL, endpoint_suffix=SERVICE_HOST_BASE,
                 request_session=None, connection_string=None, socket_timeout=None):
        '''
        :param str account_name:
            The storage account name. This is used to authenticate requests 
            signed with an account key and to construct the storage endpoint. It 
            is required unless a connection string is given.
        :param str account_key:
            The storage account key. This is used for shared key authentication. 
        :param str sas_token:
             A shared access signature token to use to authenticate requests 
             instead of the account key. If account key and sas token are both 
             specified, account key will be used to sign.
        :param bool is_emulated:
            Whether to use the emulator. Defaults to False. If specified, will 
            override all other parameters besides connection string and request 
            session.
        :param str protocol:
            The protocol to use for requests. Defaults to https.
        :param str endpoint_suffix:
            The host base component of the url, minus the account name. Defaults 
            to Azure (core.windows.net). Override this to use the China cloud 
            (core.chinacloudapi.cn).
        :param requests.Session request_session:
            The session object to use for http requests.
        :param str connection_string:
            If specified, this will override all other parameters besides 
            request session. See
            http://azure.microsoft.com/en-us/documentation/articles/storage-configure-connection-string/
            for the connection string format.
        :param int socket_timeout:
            If specified, this will override the default socket timeout. The timeout specified is in seconds.
            See DEFAULT_SOCKET_TIMEOUT in _constants.py for the default value.
        '''
        service_params = _ServiceParameters.get_service_parameters(
            'queue',
            account_name=account_name, 
            account_key=account_key, 
            sas_token=sas_token, 
            is_emulated=is_emulated, 
            protocol=protocol, 
            endpoint_suffix=endpoint_suffix,
            request_session=request_session,
            connection_string=connection_string,
            socket_timeout=socket_timeout)
            
        super(QueueService, self).__init__(service_params)

        if self.account_key:
            self.authentication = _StorageSharedKeyAuthentication(
                self.account_name,
                self.account_key,
            )
        elif self.sas_token:
            self.authentication = _StorageSASAuthentication(self.sas_token)
        else:
            raise ValueError(_ERROR_STORAGE_MISSING_INFO)

        self.encode_function = QueueMessageFormat.text_xmlencode
        self.decode_function = QueueMessageFormat.text_xmldecode
        self.key_encryption_key = None
        self.key_resolver_function = None
        self.require_encryption = False

    def generate_account_shared_access_signature(self, resource_types, permission, 
                                        expiry, start=None, ip=None, protocol=None):
        '''
        Generates a shared access signature for the queue service.
        Use the returned signature with the sas_token parameter of QueueService.

        :param ResourceTypes resource_types:
            Specifies the resource types that are accessible with the account SAS.
        :param AccountPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :return: A Shared Access Signature (sas) token.
        :rtype: str
        '''
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_account(Services.QUEUE, resource_types, permission, 
                                    expiry, start=start, ip=ip, protocol=protocol)

    def generate_queue_shared_access_signature(self, queue_name,
                                         permission=None, 
                                         expiry=None,                                       
                                         start=None,
                                         id=None,
                                         ip=None, protocol=None,):
        '''
        Generates a shared access signature for the queue.
        Use the returned signature with the sas_token parameter of QueueService.

        :param str queue_name:
            The name of the queue to create a SAS token for.
        :param QueuePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use :func:`~set_queue_acl`.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip='168.1.5.65' or sip='168.1.5.60-168.1.5.70' on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :return: A Shared Access Signature (sas) token.
        :rtype: str
        '''
        _validate_not_none('queue_name', queue_name)
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_queue(
            queue_name,
            permission=permission, 
            expiry=expiry,
            start=start, 
            id=id,
            ip=ip,
            protocol=protocol,
        )

    def get_queue_service_stats(self, timeout=None):
        '''
        Retrieves statistics related to replication for the Queue service. It is 
        only available when read-access geo-redundant replication is enabled for 
        the storage account.

        With geo-redundant replication, Azure Storage maintains your data durable 
        in two locations. In both locations, Azure Storage constantly maintains 
        multiple healthy replicas of your data. The location where you read, 
        create, update, or delete data is the primary storage account location. 
        The primary location exists in the region you choose at the time you 
        create an account via the Azure Management Azure classic portal, for 
        example, North Central US. The location to which your data is replicated 
        is the secondary location. The secondary location is automatically 
        determined based on the location of the primary; it is in a second data 
        center that resides in the same region as the primary location. Read-only 
        access is available from the secondary location, if read-access geo-redundant 
        replication is enabled for your storage account.

        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: The queue service stats.
        :rtype: :class:`~azure.storage.models.ServiceStats`
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(primary=False, secondary=True)
        request.path = _get_path()
        request.query = {
            'restype': 'service',
            'comp': 'stats',
            'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_service_stats)

    def get_queue_service_properties(self, timeout=None):
        '''
        Gets the properties of a storage account's Queue service, including
        logging, analytics and CORS rules.

        :param int timeout:
            The server timeout, expressed in seconds.
        :return: The queue service properties.
        :rtype: :class:`~azure.storage.models.ServiceProperties`
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(secondary=True)
        request.path = _get_path()
        request.query = {
            'restype': 'service',
            'comp': 'properties',
            'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_service_properties)

    def set_queue_service_properties(self, logging=None, hour_metrics=None, 
                                    minute_metrics=None, cors=None, timeout=None):
        '''
        Sets the properties of a storage account's Queue service, including
        Azure Storage Analytics. If an element (ex Logging) is left as None, the 
        existing settings on the service for that functionality are preserved. 
        For more information on Azure Storage Analytics, see 
        https://msdn.microsoft.com/en-us/library/azure/hh343270.aspx.

        :param Logging logging:
            The logging settings provide request logs.
        :param Metrics hour_metrics:
            The hour metrics settings provide a summary of request 
            statistics grouped by API in hourly aggregates for queuess.
        :param Metrics minute_metrics:
            The minute metrics settings provide request statistics 
            for each minute for queues.
        :param cors:
            You can include up to five CorsRule elements in the 
            list. If an empty list is specified, all CORS rules will be deleted, 
            and CORS will be disabled for the service. For detailed information 
            about CORS rules and evaluation logic, see 
            https://msdn.microsoft.com/en-us/library/azure/dn535601.aspx.
        :type cors: list of :class:`~azure.storage.models.CorsRule`
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path()
        request.query = {
            'restype': 'service',
            'comp': 'properties',
            'timeout': _int_to_str(timeout),
        }
        request.body = _get_request_body(
            _convert_service_properties_to_xml(logging, hour_metrics, minute_metrics, cors))
        self._perform_request(request)

    def list_queues(self, prefix=None, num_results=None, include_metadata=False, 
                    marker=None, timeout=None):
        '''
        Returns a generator to list the queues. The generator will lazily follow 
        the continuation tokens returned by the service and stop when all queues 
        have been returned or num_results is reached.

        If num_results is specified and the account has more than that number of 
        queues, the generator will have a populated next_marker field once it 
        finishes. This marker can be used to create a new generator if more 
        results are desired.

        :param str prefix:
            Filters the results to return only queues with names that begin
            with the specified prefix.
        :param int num_results:
            The maximum number of queues to return.
        :param bool include_metadata:
            Specifies that container metadata be returned in the response.
        :param str marker:
            An opaque continuation token. This value can be retrieved from the 
            next_marker field of a previous generator object if num_results was 
            specified and that generator has finished enumerating results. If 
            specified, this generator will begin returning results from the point 
            where the previous generator stopped.
        :param int timeout:
            The server timeout, expressed in seconds. This function may make multiple 
            calls to the service in which case the timeout value specified will be 
            applied to each individual call.
        '''
        include = 'metadata' if include_metadata else None
        operation_context = _OperationContext(location_lock=True)
        kwargs = {'prefix': prefix, 'max_results': num_results, 'include': include, 
                  'marker': marker, 'timeout': timeout, '_context': operation_context}
        resp = self._list_queues(**kwargs)

        return ListGenerator(resp, self._list_queues, (), kwargs)

    def _list_queues(self, prefix=None, marker=None, max_results=None,
                    include=None, timeout=None, _context=None):
        '''
        Returns a list of queues under the specified account. Makes a single list 
        request to the service. Used internally by the list_queues method.

        :param str prefix:
            Filters the results to return only queues with names that begin
            with the specified prefix.
        :param str marker:
            A token which identifies the portion of the query to be
            returned with the next query operation. The operation returns a
            next_marker element within the response body if the list returned
            was not complete. This value may then be used as a query parameter
            in a subsequent call to request the next portion of the list of
            queues. The marker value is opaque to the client.
        :param int max_results:
            The maximum number of queues to return. A single list request may 
            return up to 1000 queues and potentially a continuation token which 
            should be followed to get additional resutls.
        :param str include:
            Include this parameter to specify that the container's
            metadata be returned as part of the response body.
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(secondary=True)
        request.path = _get_path()
        request.query = {
            'comp': 'list',
            'prefix': _to_str(prefix),
            'marker': _to_str(marker),
            'maxresults': _int_to_str(max_results),
            'include': _to_str(include),
            'timeout': _int_to_str(timeout)
        }

        return self._perform_request(request, _convert_xml_to_queues, operation_context=_context)

    def create_queue(self, queue_name, metadata=None, fail_on_exist=False, timeout=None):
        '''
        Creates a queue under the given account.

        :param str queue_name:
            The name of the queue to create. A queue name must be from 3 through 
            63 characters long and may only contain lowercase letters, numbers, 
            and the dash (-) character. The first and last letters in the queue 
            must be alphanumeric. The dash (-) character cannot be the first or 
            last character. Consecutive dash characters are not permitted in the 
            queue name.
        :param metadata:
            A dict containing name-value pairs to associate with the queue as 
            metadata. Note that metadata names preserve the case with which they 
            were created, but are case-insensitive when set or read. 
        :type metadata: a dict mapping str to str 
        :param bool fail_on_exist:
            Specifies whether to throw an exception if the queue already exists.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return:
            A boolean indicating whether the queue was created. If fail_on_exist 
            was set to True, this will throw instead of returning false.
        :rtype: bool
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name)
        request.query = {'timeout': _int_to_str(timeout)}
        _add_metadata_headers(metadata, request)

        def _return_request(request):
            return request

        if not fail_on_exist:
            try:
                response = self._perform_request(request, parser=_return_request)
                if response.status == _HTTP_RESPONSE_NO_CONTENT:
                    return False
                return True
            except AzureHttpError as ex:
                _dont_fail_on_exist(ex)
                return False
        else:
            response = self._perform_request(request, parser=_return_request)
            if response.status == _HTTP_RESPONSE_NO_CONTENT:
                raise AzureConflictHttpError(
                    _ERROR_CONFLICT.format(response.message), response.status)
            return True

    def delete_queue(self, queue_name, fail_not_exist=False, timeout=None):
        '''
        Deletes the specified queue and any messages it contains.

        When a queue is successfully deleted, it is immediately marked for deletion 
        and is no longer accessible to clients. The queue is later removed from 
        the Queue service during garbage collection.

        Note that deleting a queue is likely to take at least 40 seconds to complete. 
        If an operation is attempted against the queue while it was being deleted, 
        an :class:`AzureConflictHttpError` will be thrown.

        :param str queue_name:
            The name of the queue to delete.
        :param bool fail_not_exist:
            Specifies whether to throw an exception if the queue doesn't exist.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return:
            A boolean indicating whether the queue was deleted. If fail_not_exist 
            was set to True, this will throw instead of returning false.
        :rtype: bool
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name)
        request.query = {'timeout': _int_to_str(timeout)}
        if not fail_not_exist:
            try:
                self._perform_request(request)
                return True
            except AzureHttpError as ex:
                _dont_fail_not_exist(ex)
                return False
        else:
            self._perform_request(request)
            return True

    def get_queue_metadata(self, queue_name, timeout=None):
        '''
        Retrieves user-defined metadata and queue properties on the specified
        queue. Metadata is associated with the queue as name-value pairs.

        :param str queue_name:
            The name of an existing queue.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return:
            A dictionary representing the queue metadata with an 
            approximate_message_count int property on the dict estimating the 
            number of messages in the queue.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(secondary=True)
        request.path = _get_path(queue_name)
        request.query = {
            'comp': 'metadata',
            'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_metadata_and_message_count)

    def set_queue_metadata(self, queue_name, metadata=None, timeout=None):
        '''
        Sets user-defined metadata on the specified queue. Metadata is
        associated with the queue as name-value pairs.

        :param str queue_name:
            The name of an existing queue.
        :param dict metadata:
            A dict containing name-value pairs to associate with the
            queue as metadata.
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name)
        request.query = {
            'comp': 'metadata',
            'timeout': _int_to_str(timeout),
        }
        _add_metadata_headers(metadata, request)

        self._perform_request(request)

    def exists(self, queue_name, timeout=None):
        '''
        Returns a boolean indicating whether the queue exists.

        :param str queue_name:
            The name of queue to check for existence.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return: A boolean indicating whether the queue exists.
        :rtype: bool
        '''
        try:
            self.get_queue_metadata(queue_name, timeout=timeout)
            return True
        except AzureHttpError as ex:
            _dont_fail_not_exist(ex)
            return False

    def get_queue_acl(self, queue_name, timeout=None):
        '''
        Returns details about any stored access policies specified on the
        queue that may be used with Shared Access Signatures.

        :param str queue_name:
            The name of an existing queue.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return: A dictionary of access policies associated with the queue.
        :rtype: dict of str to :class:`~azure.storage.models.AccessPolicy`
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(secondary=True)
        request.path = _get_path(queue_name)
        request.query = {
            'comp': 'acl',
            'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_signed_identifiers)

    def set_queue_acl(self, queue_name, signed_identifiers=None, timeout=None):
        '''
        Sets stored access policies for the queue that may be used with Shared 
        Access Signatures. 
        
        When you set permissions for a queue, the existing permissions are replaced. 
        To update the queue's permissions, call :func:`~get_queue_acl` to fetch 
        all access policies associated with the queue, modify the access policy 
        that you wish to change, and then call this function with the complete 
        set of data to perform the update.

        When you establish a stored access policy on a queue, it may take up to 
        30 seconds to take effect. During this interval, a shared access signature 
        that is associated with the stored access policy will throw an 
        :class:`AzureHttpError` until the access policy becomes active.

        :param str queue_name:
            The name of an existing queue.
        :param signed_identifiers:
            A dictionary of access policies to associate with the queue. The 
            dictionary may contain up to 5 elements. An empty dictionary 
            will clear the access policies set on the service. 
        :type signed_identifiers: dict of str to :class:`~azure.storage.models.AccessPolicy`
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        _validate_not_none('queue_name', queue_name)
        _validate_access_policies(signed_identifiers)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name)
        request.query = {
            'comp': 'acl',
            'timeout': _int_to_str(timeout),
        }
        request.body = _get_request_body(
            _convert_signed_identifiers_to_xml(signed_identifiers))
        self._perform_request(request)

    def put_message(self, queue_name, content, visibility_timeout=None,
                    time_to_live=None, timeout=None):
        '''
        Adds a new message to the back of the message queue. 

        The visibility timeout specifies the time that the message will be 
        invisible. After the timeout expires, the message will become visible. 
        If a visibility timeout is not specified, the default value of 0 is used.

        The message time-to-live specifies how long a message will remain in the 
        queue. The message will be deleted from the queue when the time-to-live 
        period expires.

        If the key-encryption-key field is set on the local service object, this method will
        encrypt the content before uploading.

        :param str queue_name:
            The name of the queue to put the message into.
        :param obj content:
            Message content. Allowed type is determined by the encode_function 
            set on the service. Default is str. The encoded message can be up to 
            64KB in size.
        :param int visibility_timeout:
            If not specified, the default value is 0. Specifies the
            new visibility timeout value, in seconds, relative to server time.
            The value must be larger than or equal to 0, and cannot be
            larger than 7 days. The visibility timeout of a message cannot be
            set to a value later than the expiry time. visibility_timeout
            should be set to a value smaller than the time-to-live value.
        :param int time_to_live:
            Specifies the time-to-live interval for the message, in
            seconds. The maximum time-to-live allowed is 7 days. If this
            parameter is omitted, the default time-to-live is 7 days.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return:
            A :class:`~azure.storage.queue.models.QueueMessage` object.
            This object is also populated with the content although it is not
            returned from the service.
        :rtype: :class:`~azure.storage.queue.models.QueueMessage`
        '''

        _validate_encryption_required(self.require_encryption, self.key_encryption_key)

        _validate_not_none('queue_name', queue_name)
        _validate_not_none('content', content)
        request = HTTPRequest()
        request.method = 'POST'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name, True)
        request.query = {
            'visibilitytimeout': _to_str(visibility_timeout),
            'messagettl': _to_str(time_to_live),
            'timeout': _int_to_str(timeout)
        }

        request.body = _get_request_body(_convert_queue_message_xml(content, self.encode_function,
                                                                    self.key_encryption_key))

        message_list = self._perform_request(request, _convert_xml_to_queue_messages,
                                     [self.decode_function, False,
                                      None, None, content])
        return message_list[0]

    def get_messages(self, queue_name, num_messages=None,
                     visibility_timeout=None, timeout=None):
        '''
        Retrieves one or more messages from the front of the queue.

        When a message is retrieved from the queue, the response includes the message 
        content and a pop_receipt value, which is required to delete the message. 
        The message is not automatically deleted from the queue, but after it has 
        been retrieved, it is not visible to other clients for the time interval 
        specified by the visibility_timeout parameter.

        If the key-encryption-key or resolver field is set on the local service object, the messages will be
        decrypted before being returned.

        :param str queue_name:
            The name of the queue to get messages from.
        :param int num_messages:
            A nonzero integer value that specifies the number of
            messages to retrieve from the queue, up to a maximum of 32. If
            fewer are visible, the visible messages are returned. By default,
            a single message is retrieved from the queue with this operation.
        :param int visibility_timeout:
            Specifies the new visibility timeout value, in seconds, relative
            to server time. The new value must be larger than or equal to 1
            second, and cannot be larger than 7 days. The visibility timeout of 
            a message can be set to a value later than the expiry time.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return: A :class:`~azure.storage.queue.models.QueueMessage` object representing the information passed.
        :rtype: list of :class:`~azure.storage.queue.models.QueueMessage`
        '''
        _validate_decryption_required(self.require_encryption, self.key_encryption_key,
                                      self.key_resolver_function)

        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name, True)
        request.query = {
            'numofmessages': _to_str(num_messages),
            'visibilitytimeout': _to_str(visibility_timeout),
            'timeout': _int_to_str(timeout)
        }

        return self._perform_request(request, _convert_xml_to_queue_messages,
                                     [self.decode_function, self.require_encryption,
                                      self.key_encryption_key, self.key_resolver_function])

    def peek_messages(self, queue_name, num_messages=None, timeout=None):
        '''
        Retrieves one or more messages from the front of the queue, but does
        not alter the visibility of the message.

        Only messages that are visible may be retrieved. When a message is retrieved 
        for the first time with a call to get_messages, its dequeue_count property 
        is set to 1. If it is not deleted and is subsequently retrieved again, the 
        dequeue_count property is incremented. The client may use this value to 
        determine how many times a message has been retrieved. Note that a call 
        to peek_messages does not increment the value of DequeueCount, but returns 
        this value for the client to read.

        If the key-encryption-key or resolver field is set on the local service object, the messages will be
        decrypted before being returned.

        :param str queue_name:
            The name of the queue to peek messages from.
        :param int num_messages:
            A nonzero integer value that specifies the number of
            messages to peek from the queue, up to a maximum of 32. By default,
            a single message is peeked from the queue with this operation.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return: 
            A list of :class:`~azure.storage.queue.models.QueueMessage` objects. Note that 
            time_next_visible and pop_receipt will not be populated as peek does 
            not pop the message and can only retrieve already visible messages.
        :rtype: list of :class:`~azure.storage.queue.models.QueueMessage`
        '''

        _validate_decryption_required(self.require_encryption, self.key_encryption_key,
                                      self.key_resolver_function)

        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations(secondary=True)
        request.path = _get_path(queue_name, True)
        request.query = {
            'peekonly': 'true',
            'numofmessages': _to_str(num_messages),
            'timeout': _int_to_str(timeout)
        }

        return self._perform_request(request, _convert_xml_to_queue_messages,
                                     [self.decode_function, self.require_encryption,
                                      self.key_encryption_key, self.key_resolver_function])

    def delete_message(self, queue_name, message_id, pop_receipt, timeout=None):
        '''
        Deletes the specified message.

        Normally after a client retrieves a message with the get_messages operation, 
        the client is expected to process and delete the message. To delete the 
        message, you must have two items of data: id and pop_receipt. The 
        id is returned from the previous get_messages operation. The 
        pop_receipt is returned from the most recent :func:`~get_messages` or 
        :func:`~update_message` operation. In order for the delete_message operation 
        to succeed, the pop_receipt specified on the request must match the 
        pop_receipt returned from the :func:`~get_messages` or :func:`~update_message` 
        operation. 

        :param str queue_name:
            The name of the queue from which to delete the message.
        :param str message_id:
            The message id identifying the message to delete.
        :param str pop_receipt:
            A valid pop receipt value returned from an earlier call
            to the :func:`~get_messages` or :func:`~update_message`.
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        _validate_not_none('queue_name', queue_name)
        _validate_not_none('message_id', message_id)
        _validate_not_none('pop_receipt', pop_receipt)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name, True, message_id)
        request.query = {
            'popreceipt': _to_str(pop_receipt),
            'timeout': _int_to_str(timeout)
        }
        self._perform_request(request)

    def clear_messages(self, queue_name, timeout=None):
        '''
        Deletes all messages from the specified queue.

        :param str queue_name:
            The name of the queue whose messages to clear.
        :param int timeout:
            The server timeout, expressed in seconds.
        '''
        _validate_not_none('queue_name', queue_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name, True)
        request.query = {'timeout': _int_to_str(timeout)}
        self._perform_request(request)

    def update_message(self, queue_name, message_id, pop_receipt, visibility_timeout, 
                       content=None, timeout=None):
        '''
        Updates the visibility timeout of a message. You can also use this
        operation to update the contents of a message.

        This operation can be used to continually extend the invisibility of a 
        queue message. This functionality can be useful if you want a worker role 
        to "lease" a queue message. For example, if a worker role calls get_messages 
        and recognizes that it needs more time to process a message, it can 
        continually extend the message's invisibility until it is processed. If 
        the worker role were to fail during processing, eventually the message 
        would become visible again and another worker role could process it.

        If the key-encryption-key field is set on the local service object, this method will
        encrypt the content before uploading.

        :param str queue_name:
            The name of the queue containing the message to update.
        :param str message_id:
            The message id identifying the message to update.
        :param str pop_receipt:
            A valid pop receipt value returned from an earlier call
            to the :func:`~get_messages` or :func:`~update_message` operation.
        :param int visibility_timeout:
            Specifies the new visibility timeout value, in seconds,
            relative to server time. The new value must be larger than or equal
            to 0, and cannot be larger than 7 days. The visibility timeout of a
            message cannot be set to a value later than the expiry time. A
            message can be updated until it has been deleted or has expired.
        :param obj content:
            Message content. Allowed type is determined by the encode_function 
            set on the service. Default is str.
        :param int timeout:
            The server timeout, expressed in seconds.
        :return: 
            A list of :class:`~azure.storage.queue.models.QueueMessage` objects. For convenience,
            this object is also populated with the content, although it is not returned by the service.
        :rtype: list of :class:`~azure.storage.queue.models.QueueMessage`
        '''

        _validate_encryption_required(self.require_encryption, self.key_encryption_key)

        _validate_not_none('queue_name', queue_name)
        _validate_not_none('message_id', message_id)
        _validate_not_none('pop_receipt', pop_receipt)
        _validate_not_none('visibility_timeout', visibility_timeout)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(queue_name, True, message_id)
        request.query = {
            'popreceipt': _to_str(pop_receipt),
            'visibilitytimeout': _int_to_str(visibility_timeout),
            'timeout': _int_to_str(timeout)
        }

        if content is not None:
            request.body = _get_request_body(_convert_queue_message_xml(content, self.encode_function,
                                                                        self.key_encryption_key))

        return self._perform_request(request, _parse_queue_message_from_headers)
