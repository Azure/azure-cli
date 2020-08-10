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
from azure.common import AzureHttpError
from .._error import (
    _dont_fail_not_exist,
    _dont_fail_on_exist,
    _validate_not_none,
    _validate_type_bytes,
    _ERROR_VALUE_NEGATIVE,
    _ERROR_STORAGE_MISSING_INFO,
    _ERROR_EMULATOR_DOES_NOT_SUPPORT_FILES,
    _ERROR_PARALLEL_NOT_SEEKABLE,
    _validate_access_policies,
)
from .._common_conversion import (
    _int_to_str,
    _to_str,
    _get_content_md5,
)
from .._serialization import (
    _get_request_body,
    _get_data_bytes_only,
    _convert_signed_identifiers_to_xml,
    _convert_service_properties_to_xml,
    _add_metadata_headers,
)
from .._deserialization import (
    _convert_xml_to_service_properties,
    _convert_xml_to_signed_identifiers,
    _get_download_size,
    _parse_metadata,
    _parse_properties,
    _parse_length_from_content_range,
)
from ..models import (
    Services,
    ListGenerator,
    _OperationContext,
)
from .models import (
    File,
    FileProperties,
)
from .._http import HTTPRequest
from ._upload_chunking import _upload_file_chunks
from ._download_chunking import _download_file_chunks
from .._auth import (
    _StorageSharedKeyAuthentication,
    _StorageSASAuthentication,
)
from .._connection import _ServiceParameters
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
    DEV_ACCOUNT_NAME,
)
from ._serialization import (
    _get_path,
    _validate_and_format_range_headers,
)
from ._deserialization import (
    _convert_xml_to_shares,
    _convert_xml_to_directories_and_files,
    _convert_xml_to_ranges,
    _convert_xml_to_share_stats,
    _parse_file,
    _parse_share,
    _parse_directory,
)
from ..sharedaccesssignature import (
    SharedAccessSignature,
)
from ..storageclient import StorageClient
from os import path
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO

class FileService(StorageClient):

    '''
    The Server Message Block (SMB) protocol is the preferred file share protocol
    used on premise today. The Microsoft Azure File service enables customers to
    leverage the availability and scalability of Azure's Cloud Infrastructure as
    a Service (IaaS) SMB without having to rewrite SMB client applications.

    The Azure File service also offers a compelling alternative to traditional
    Direct Attached Storage (DAS) and Storage Area Network (SAN) solutions, which
    are often complex and expensive to install, configure, and operate. 

    :ivar int MAX_SINGLE_GET_SIZE: 
        The size of the first range get performed by get_file_to_* methods if 
        max_connections is greater than 1. Less data will be returned if the 
        file is smaller than this.
    :ivar int MAX_CHUNK_GET_SIZE: 
        The size of subsequent range gets performed by get_file_to_* methods if 
        max_connections is greater than 1 and the file is larger than MAX_SINGLE_GET_SIZE. 
        Less data will be returned if the remainder of the file is smaller than 
        this. If this is set to larger than 4MB, content_validation will throw an 
        error if enabled. However, if content_validation is not desired a size 
        greater than 4MB may be optimal. Setting this below 4MB is not recommended.
    :ivar int MAX_RANGE_SIZE: 
        The size of the ranges put by create_file_from_* methods. Smaller ranges 
        may be put if there is less data provided. The maximum range size the service 
        supports is 4MB.
    '''
    MAX_SINGLE_GET_SIZE = 32 * 1024 * 1024
    MAX_CHUNK_GET_SIZE = 8 * 1024 * 1024
    MAX_RANGE_SIZE = 4 * 1024 * 1024

    def __init__(self, account_name=None, account_key=None, sas_token=None, 
                 protocol=DEFAULT_PROTOCOL, endpoint_suffix=SERVICE_HOST_BASE, 
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
            'file',
            account_name=account_name, 
            account_key=account_key, 
            sas_token=sas_token, 
            protocol=protocol, 
            endpoint_suffix=endpoint_suffix,
            request_session=request_session,
            connection_string=connection_string,
            socket_timeout=socket_timeout)
            
        super(FileService, self).__init__(service_params)

        if self.account_name == DEV_ACCOUNT_NAME:
            raise ValueError(_ERROR_EMULATOR_DOES_NOT_SUPPORT_FILES)

        if self.account_key:
            self.authentication = _StorageSharedKeyAuthentication(
                self.account_name,
                self.account_key,
            )
        elif self.sas_token:
            self.authentication = _StorageSASAuthentication(self.sas_token)
        else:
            raise ValueError(_ERROR_STORAGE_MISSING_INFO)

    def make_file_url(self, share_name, directory_name, file_name, 
                      protocol=None, sas_token=None):
        '''
        Creates the url to access a file.

        :param str share_name:
            Name of share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file.
        :param str protocol:
            Protocol to use: 'http' or 'https'. If not specified, uses the
            protocol specified when FileService was initialized.
        :param str sas_token:
            Shared access signature token created with
            generate_shared_access_signature.
        :return: file access URL.
        :rtype: str
        '''

        if directory_name is None:
            url = '{}://{}/{}/{}'.format(
                protocol or self.protocol,
                self.primary_endpoint,
                share_name,
                file_name,
            )
        else:
            url = '{}://{}/{}/{}/{}'.format(
                protocol or self.protocol,
                self.primary_endpoint,
                share_name,
                directory_name,
                file_name,
            )

        if sas_token:
            url += '?' + sas_token

        return url

    def generate_account_shared_access_signature(self, resource_types, permission, 
                                        expiry, start=None, ip=None, protocol=None):
        '''
        Generates a shared access signature for the file service.
        Use the returned signature with the sas_token parameter of the FileService.

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
            Specifies the protocol permitted for a request made. Possible values are
            both HTTPS and HTTP (https,http) or HTTPS only (https). The default value
            is https,http. Note that HTTP only is not a permitted value.
        :return: A Shared Access Signature (sas) token.
        :rtype: str
        '''
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_account(Services.FILE, resource_types, permission, 
                                    expiry, start=start, ip=ip, protocol=protocol)

    def generate_share_shared_access_signature(self, share_name, 
                                         permission=None, 
                                         expiry=None,
                                         start=None, 
                                         id=None,
                                         ip=None,
                                         protocol=None,
                                         cache_control=None,
                                         content_disposition=None,
                                         content_encoding=None,
                                         content_language=None,
                                         content_type=None):
        '''
        Generates a shared access signature for the share.
        Use the returned signature with the sas_token parameter of FileService.

        :param str share_name:
            Name of share.
        :param SharePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, create, write, delete, list.
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
            stored access policy. To create a stored access policy, use :func:`~set_share_acl`.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. Possible values are
            both HTTPS and HTTP (https,http) or HTTPS only (https). The default value
            is https,http. Note that HTTP only is not a permitted value.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        :return: A Shared Access Signature (sas) token.
        :rtype: str
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_share(
            share_name,
            permission, 
            expiry,
            start=start, 
            id=id,
            ip=ip,
            protocol=protocol,
            cache_control=cache_control,
            content_disposition=content_disposition,
            content_encoding=content_encoding,
            content_language=content_language,
            content_type=content_type,
        )

    def generate_file_shared_access_signature(self, share_name, 
                                         directory_name=None, 
                                         file_name=None,
                                         permission=None, 
                                         expiry=None,
                                         start=None, 
                                         id=None,
                                         ip=None,
                                         protocol=None,
                                         cache_control=None,
                                         content_disposition=None,
                                         content_encoding=None,
                                         content_language=None,
                                         content_type=None):
        '''
        Generates a shared access signature for the file.
        Use the returned signature with the sas_token parameter of FileService.

        :param str share_name:
            Name of share.
        :param str directory_name:
            Name of directory. SAS tokens cannot be created for directories, so 
            this parameter should only be present if file_name is provided.
        :param str file_name:
            Name of file.
        :param FilePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, create, write, delete, list.
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
            stored access policy. To create a stored access policy, use 
            set_file_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. Possible values are
            both HTTPS and HTTP (https,http) or HTTPS only (https). The default value
            is https,http. Note that HTTP only is not a permitted value.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        :return: A Shared Access Signature (sas) token.
        :rtype: str
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_file(
            share_name,
            directory_name,
            file_name,
            permission, 
            expiry,
            start=start, 
            id=id,
            ip=ip,
            protocol=protocol,
            cache_control=cache_control,
            content_disposition=content_disposition,
            content_encoding=content_encoding,
            content_language=content_language,
            content_type=content_type,
        )

    def set_file_service_properties(self, hour_metrics=None, minute_metrics=None, 
                                    cors=None, timeout=None):
        '''
        Sets the properties of a storage account's File service, including
        Azure Storage Analytics. If an element (ex HourMetrics) is left as None, the 
        existing settings on the service for that functionality are preserved.

        :param Metrics hour_metrics:
            The hour metrics settings provide a summary of request 
            statistics grouped by API in hourly aggregates for files.
        :param Metrics minute_metrics:
            The minute metrics settings provide request statistics 
            for each minute for files.
        :param cors:
            You can include up to five CorsRule elements in the 
            list. If an empty list is specified, all CORS rules will be deleted, 
            and CORS will be disabled for the service.
        :type cors: list of :class:`~azure.storage.models.CorsRule`
        :param int timeout:
            The timeout parameter is expressed in seconds.
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
            _convert_service_properties_to_xml(None, hour_metrics, minute_metrics, cors))

        self._perform_request(request)

    def get_file_service_properties(self, timeout=None):
        '''
        Gets the properties of a storage account's File service, including
        Azure Storage Analytics.

        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: The file service properties.
        :rtype:
            :class:`~azure.storage.models.ServiceProperties`
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path()
        request.query = {
             'restype': 'service',
             'comp': 'properties',
             'timeout': _int_to_str(timeout),         
        }

        return self._perform_request(request, _convert_xml_to_service_properties)

    def list_shares(self, prefix=None, marker=None, num_results=None, 
                    include_metadata=False, timeout=None):
        '''
        Returns a generator to list the shares under the specified account.
        The generator will lazily follow the continuation tokens returned by
        the service and stop when all shares have been returned or num_results 
        is reached.

        If num_results is specified and the account has more than that number of 
        shares, the generator will have a populated next_marker field once it 
        finishes. This marker can be used to create a new generator if more 
        results are desired.

        :param str prefix:
            Filters the results to return only shares whose names
            begin with the specified prefix.
        :param int num_results:
            Specifies the maximum number of shares to return.
        :param bool include_metadata:
            Specifies that share metadata be returned in the response.
        :param str marker:
            An opaque continuation token. This value can be retrieved from the 
            next_marker field of a previous generator object if num_results was 
            specified and that generator has finished enumerating results. If 
            specified, this generator will begin returning results from the point 
            where the previous generator stopped.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        include = 'metadata' if include_metadata else None
        operation_context = _OperationContext(location_lock=True)
        kwargs = {'prefix': prefix, 'marker': marker, 'max_results': num_results, 
                'include': include, 'timeout': timeout, '_context': operation_context}
        resp = self._list_shares(**kwargs)

        return ListGenerator(resp, self._list_shares, (), kwargs)

    def _list_shares(self, prefix=None, marker=None, max_results=None, 
                     include=None, timeout=None, _context=None):
        '''
        Returns a list of the shares under the specified account.

        :param str prefix:
            Filters the results to return only shares whose names
            begin with the specified prefix.
        :param str marker:
            A string value that identifies the portion of the list
            to be returned with the next list operation. The operation returns
            a next_marker value within the response body if the list returned was
            not complete. The marker value may then be used in a subsequent
            call to request the next set of list items. The marker value is
            opaque to the client.
        :param int max_results:
            Specifies the maximum number of shares to return. A single list
            request may return up to 1000 shares and potentially a continuation
            token which should be followed to get additional resutls.
        :param string include:
            Include this parameter to specify that the share's
            metadata be returned as part of the response body. set this
            parameter to string 'metadata' to get share's metadata.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path()
        request.query = {
             'comp': 'list',
             'prefix': _to_str(prefix),
             'marker': _to_str(marker),
             'maxresults': _int_to_str(max_results),
             'include': _to_str(include),
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_shares, operation_context=_context)

    def create_share(self, share_name, metadata=None, quota=None,
                     fail_on_exist=False, timeout=None):
        '''
        Creates a new share under the specified account. If the share
        with the same name already exists, the operation fails on the
        service. By default, the exception is swallowed by the client.
        To expose the exception, specify True for fail_on_exists.

        :param str share_name:
            Name of share to create.
        :param metadata:
            A dict with name_value pairs to associate with the
            share as metadata. Example:{'Category':'test'}
        :type metadata: a dict of str to str:
        :param int quota:
            Specifies the maximum size of the share, in gigabytes. Must be 
            greater than 0, and less than or equal to 5TB (5120).
        :param bool fail_on_exist:
            Specify whether to throw an exception when the share exists.
            False by default.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if share is created, False if share already exists.
        :rtype: bool
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'timeout': _int_to_str(timeout),
        }
        request.headers = {
            'x-ms-share-quota': _int_to_str(quota)
        }
        _add_metadata_headers(metadata, request)

        if not fail_on_exist:
            try:
                self._perform_request(request)
                return True
            except AzureHttpError as ex:
                _dont_fail_on_exist(ex)
                return False
        else:
            self._perform_request(request)
            return True

    def get_share_properties(self, share_name, timeout=None):
        '''
        Returns all user-defined metadata and system properties for the
        specified share. The data returned does not include the shares's
        list of files or directories.

        :param str share_name:
            Name of existing share.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A Share that exposes properties and metadata.
        :rtype: :class:`.Share`
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_share, [share_name])

    def set_share_properties(self, share_name, quota, timeout=None):
        '''
        Sets service-defined properties for the specified share.

        :param str share_name:
            Name of existing share.
        :param int quota:
            Specifies the maximum size of the share, in gigabytes. Must be 
            greater than 0, and less than or equal to 5 TB (5120 GB).
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('quota', quota)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'properties',
             'timeout': _int_to_str(timeout),
        }
        request.headers = { 
            'x-ms-share-quota': _int_to_str(quota)
        }

        self._perform_request(request)

    def get_share_metadata(self, share_name, timeout=None):
        '''
        Returns all user-defined metadata for the specified share.

        :param str share_name:
            Name of existing share.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            A dictionary representing the share metadata name, value pairs.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_metadata)

    def set_share_metadata(self, share_name, metadata=None, timeout=None):
        '''
        Sets one or more user-defined name-value pairs for the specified
        share. Each call to this operation replaces all existing metadata
        attached to the share. To remove all metadata from the share,
        call this operation with no metadata dict.

        :param str share_name:
            Name of existing share.
        :param metadata:
            A dict containing name-value pairs to associate with the share as 
            metadata. Example: {'category':'test'}
        :type metadata: a dict mapping str to str
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }
        _add_metadata_headers(metadata, request)

        self._perform_request(request)

    def get_share_acl(self, share_name, timeout=None):
        '''
        Gets the permissions for the specified share.

        :param str share_name:
            Name of existing share.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A dictionary of access policies associated with the share.
        :rtype: dict of str to :class:`.AccessPolicy`
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'acl',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_signed_identifiers)

    def set_share_acl(self, share_name, signed_identifiers=None, timeout=None):
        '''
        Sets the permissions for the specified share or stored access 
        policies that may be used with Shared Access Signatures.

        :param str share_name:
            Name of existing share.
        :param signed_identifiers:
            A dictionary of access policies to associate with the share. The 
            dictionary may contain up to 5 elements. An empty dictionary 
            will clear the access policies set on the service. 
        :type signed_identifiers: dict of str to :class:`.AccessPolicy`
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_access_policies(signed_identifiers)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'acl',
             'timeout': _int_to_str(timeout),
        }
        request.body = _get_request_body(
            _convert_signed_identifiers_to_xml(signed_identifiers))

        self._perform_request(request)

    def get_share_stats(self, share_name, timeout=None):
        '''
        Gets the approximate size of the data stored on the share,
        rounded up to the nearest gigabyte.
        
        Note that this value may not include all recently created
        or recently resized files.

        :param str share_name:
            Name of existing share.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: the approximate size of the data stored on the share.
        :rtype: int
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'comp': 'stats',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_share_stats)

    def delete_share(self, share_name, fail_not_exist=False, timeout=None):
        '''
        Marks the specified share for deletion. If the share
        does not exist, the operation fails on the service. By 
        default, the exception is swallowed by the client.
        To expose the exception, specify True for fail_not_exist.

        :param str share_name:
            Name of share to delete.
        :param bool fail_not_exist:
            Specify whether to throw an exception when the share doesn't
            exist. False by default.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if share is deleted, False share doesn't exist.
        :rtype: bool
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name)
        request.query = {
             'restype': 'share',
             'timeout': _int_to_str(timeout),
        }

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

    def create_directory(self, share_name, directory_name, metadata=None,
                         fail_on_exist=False, timeout=None):
        '''
        Creates a new directory under the specified share or parent directory. 
        If the directory with the same name already exists, the operation fails
        on the service. By default, the exception is swallowed by the client.
        To expose the exception, specify True for fail_on_exists.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            Name of directory to create, including the path to the parent 
            directory.
        :param metadata:
            A dict with name_value pairs to associate with the
            share as metadata. Example:{'Category':'test'}
        :type metadata: dict of str to str:
        :param bool fail_on_exist:
            specify whether to throw an exception when the directory exists.
            False by default.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if directory is created, False if directory already exists.
        :rtype: bool
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('directory_name', directory_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'timeout': _int_to_str(timeout),
        }
        _add_metadata_headers(metadata, request)

        if not fail_on_exist:
            try:
                self._perform_request(request)
                return True
            except AzureHttpError as ex:
                _dont_fail_on_exist(ex)
                return False
        else:
            self._perform_request(request)
            return True

    def delete_directory(self, share_name, directory_name,
                         fail_not_exist=False, timeout=None):
        '''
        Deletes the specified empty directory. Note that the directory must
        be empty before it can be deleted. Attempting to delete directories 
        that are not empty will fail.

        If the directory does not exist, the operation fails on the
        service. By default, the exception is swallowed by the client.
        To expose the exception, specify True for fail_not_exist.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            Name of directory to delete, including the path to the parent 
            directory.
        :param bool fail_not_exist:
            Specify whether to throw an exception when the directory doesn't
            exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if directory is deleted, False otherwise.
        :rtype: bool
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('directory_name', directory_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'timeout': _int_to_str(timeout),
        }

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

    def get_directory_properties(self, share_name, directory_name, timeout=None):
        '''
        Returns all user-defined metadata and system properties for the
        specified directory. The data returned does not include the directory's
        list of files.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
           The path to an existing directory.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: properties for the specified directory within a directory object.
        :rtype: :class:`~azure.storage.file.models.Directory`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('directory_name', directory_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_directory, [directory_name])

    def get_directory_metadata(self, share_name, directory_name, timeout=None):
        '''
        Returns all user-defined metadata for the specified directory.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            A dictionary representing the directory metadata name, value pairs.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('directory_name', directory_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_metadata)

    def set_directory_metadata(self, share_name, directory_name, metadata=None, timeout=None):
        '''
        Sets one or more user-defined name-value pairs for the specified
        directory. Each call to this operation replaces all existing metadata
        attached to the directory. To remove all metadata from the directory,
        call this operation with no metadata dict.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param metadata:
            A dict containing name-value pairs to associate with the directory
            as metadata. Example: {'category':'test'}
        :type metadata: A dict mapping str to str.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('directory_name', directory_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }
        _add_metadata_headers(metadata, request)

        self._perform_request(request)

    def list_directories_and_files(self, share_name, directory_name=None,
                                   num_results=None, marker=None, timeout=None,
                                   prefix=None):

        '''
        Returns a generator to list the directories and files under the specified share.
        The generator will lazily follow the continuation tokens returned by
        the service and stop when all directories and files have been returned or
        num_results is reached.

        If num_results is specified and the share has more than that number of 
        files and directories, the generator will have a populated next_marker 
        field once it finishes. This marker can be used to create a new generator 
        if more results are desired.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param int num_results:
            Specifies the maximum number of files to return,
            including all directory elements. If the request does not specify
            num_results or specifies a value greater than 5,000, the server will
            return up to 5,000 items. Setting num_results to a value less than
            or equal to zero results in error response code 400 (Bad Request).
        :param str marker:
            An opaque continuation token. This value can be retrieved from the 
            next_marker field of a previous generator object if num_results was 
            specified and that generator has finished enumerating results. If 
            specified, this generator will begin returning results from the point 
            where the previous generator stopped.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :param str prefix:
            List only the files and/or directories with the given prefix.
        '''
        operation_context = _OperationContext(location_lock=True)
        args = (share_name, directory_name)
        kwargs = {'marker': marker, 'max_results': num_results, 'timeout': timeout,
                  '_context': operation_context, 'prefix': prefix}

        resp = self._list_directories_and_files(*args, **kwargs)

        return ListGenerator(resp, self._list_directories_and_files, args, kwargs)

    def _list_directories_and_files(self, share_name, directory_name=None,
                                   marker=None, max_results=None, timeout=None,
                                    prefix=None, _context=None):

        '''
        Returns a list of the directories and files under the specified share.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str marker:
            A string value that identifies the portion of the list
            to be returned with the next list operation. The operation returns
            a next_marker value within the response body if the list returned was
            not complete. The marker value may then be used in a subsequent
            call to request the next set of list items. The marker value is
            opaque to the client.
        :param int max_results:
            Specifies the maximum number of files to return,
            including all directory elements. If the request does not specify
            max_results or specifies a value greater than 5,000, the server will
            return up to 5,000 items. Setting max_results to a value less than
            or equal to zero results in error response code 400 (Bad Request).
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :param str prefix:
            List only the files and/or directories with the given prefix.
        '''
        _validate_not_none('share_name', share_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name)
        request.query = {
             'restype': 'directory',
             'comp': 'list',
             'prefix': _to_str(prefix),
             'marker': _to_str(marker),
             'maxresults': _int_to_str(max_results),
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _convert_xml_to_directories_and_files, 
                                     operation_context=_context)

    def get_file_properties(self, share_name, directory_name, file_name, timeout=None):
        '''
        Returns all user-defined metadata, standard HTTP properties, and
        system properties for the file. Returns an instance of :class:`.File` with
        :class:`.FileProperties` and a metadata dict.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: a file object including properties and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'HEAD'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = { 'timeout': _int_to_str(timeout)}

        return self._perform_request(request, _parse_file, [file_name])

    def exists(self, share_name, directory_name=None, file_name=None, timeout=None):
        '''
        Returns a boolean indicating whether the share exists if only share name is
        given. If directory_name is specificed a boolean will be returned indicating
        if the directory exists. If file_name is specified as well, a boolean will be
        returned indicating if the file exists.

        :param str share_name:
            Name of a share.
        :param str directory_name:
            The path to a directory.
        :param str file_name:
            Name of a file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A boolean indicating whether the resource exists.
        :rtype: bool
        '''
        _validate_not_none('share_name', share_name)
        try:
            if file_name is not None:
                self.get_file_properties(share_name, directory_name, file_name, timeout=timeout)
            elif directory_name is not None:
                self.get_directory_properties(share_name, directory_name, timeout=timeout)
            else:
                self.get_share_properties(share_name, timeout=timeout)
            return True
        except AzureHttpError as ex:
            _dont_fail_not_exist(ex)
            return False

    def resize_file(self, share_name, directory_name, 
                    file_name, content_length, timeout=None):
        '''
        Resizes a file to the specified size. If the specified byte
        value is less than the current size of the file, then all
        ranges above the specified byte value are cleared.
        
        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int content_length:
            The length to resize the file to.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('content_length', content_length)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'properties',
             'timeout': _int_to_str(timeout),
        }
        request.headers = {
             'x-ms-content-length': _to_str(content_length)
        }

        self._perform_request(request)

    def set_file_properties(self, share_name, directory_name, file_name, 
                            content_settings, timeout=None):
        '''
        Sets system properties on the file. If one property is set for the
        content_settings, all properties will be overriden.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used to set the file properties.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('content_settings', content_settings)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'properties',
             'timeout': _int_to_str(timeout),
        }
        request.headers = content_settings._to_headers()

        self._perform_request(request)

    def get_file_metadata(self, share_name, directory_name, file_name, timeout=None):
        '''
        Returns all user-defined metadata for the specified file.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            A dictionary representing the file metadata name, value pairs.
        :rtype: dict mapping str to str.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }

        return self._perform_request(request, _parse_metadata)

    def set_file_metadata(self, share_name, directory_name, 
                          file_name, metadata=None, timeout=None):
        '''
        Sets user-defined metadata for the specified file as one or more
        name-value pairs.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param metadata:
            Dict containing name and value pairs. Each call to this operation
            replaces all existing metadata attached to the file. To remove all
            metadata from the file, call this operation with no metadata headers.
        :type metadata: dict mapping str to str
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'metadata',
             'timeout': _int_to_str(timeout),
        }
        _add_metadata_headers(metadata, request)

        self._perform_request(request)

    def copy_file(self, share_name, directory_name, file_name, copy_source,
                  metadata=None, timeout=None):
        '''
        Copies a file asynchronously. This operation returns a copy operation 
        properties object, including a copy ID you can use to check or abort the 
        copy operation. The File service copies files on a best-effort basis.

        If the destination file exists, it will be overwritten. The destination 
        file cannot be modified while the copy operation is in progress.

        :param str share_name:
            Name of the destination share. The share must exist.
        :param str directory_name:
            Name of the destination directory. The directory must exist.
        :param str file_name:
            Name of the destination file. If the destination file exists, it will 
            be overwritten. Otherwise, it will be created.
        :param str copy_source:
            A URL of up to 2 KB in length that specifies an Azure file or blob. 
            The value should be URL-encoded as it would appear in a request URI. 
            If the source is in another account, the source must either be public 
            or must be authenticated via a shared access signature. If the source 
            is public, no authentication is required.
            Examples:
            https://myaccount.file.core.windows.net/myshare/mydir/myfile
            https://otheraccount.file.core.windows.net/myshare/mydir/myfile?sastoken
        :param metadata:
            Name-value pairs associated with the file as metadata. If no name-value 
            pairs are specified, the operation will copy the metadata from the 
            source blob or file to the destination file. If one or more name-value 
            pairs are specified, the destination file is created with the specified 
            metadata, and the metadata is not copied from the source blob or file. 
        :type metadata: A dict mapping str to str.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: Copy operation properties such as status, source, and ID.
        :rtype: :class:`~azure.storage.file.models.CopyProperties`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('copy_source', copy_source)

        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = { 'timeout': _int_to_str(timeout)}
        request.headers = {
             'x-ms-copy-source': _to_str(copy_source),
        }
        _add_metadata_headers(metadata, request)

        return self._perform_request(request, _parse_properties, [FileProperties]).copy

    def abort_copy_file(self, share_name, directory_name, file_name, copy_id, timeout=None):
        '''
         Aborts a pending copy_file operation, and leaves a destination file
         with zero length and full metadata.

        :param str share_name:
             Name of destination share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
             Name of destination file.
        :param str copy_id:
            Copy identifier provided in the copy.id of the original
            copy_file operation.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('copy_id', copy_id)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'copy',
             'copyid': _to_str(copy_id),
             'timeout': _int_to_str(timeout),
        }
        request.headers = {
             'x-ms-copy-action': 'abort',
        }

        self._perform_request(request)

    def delete_file(self, share_name, directory_name, file_name, timeout=None):
        '''
        Marks the specified file for deletion. The file is later
        deleted during garbage collection.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = { 'timeout': _int_to_str(timeout)}

        self._perform_request(request)

    def create_file(self, share_name, directory_name, file_name,
                    content_length, content_settings=None, metadata=None, 
                    timeout=None):
        '''
        Creates a new file.

        See create_file_from_* for high level functions that handle the
        creation and upload of large files with automatic chunking and
        progress notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file to create or update.
        :param int content_length:
            Length of the file in bytes.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used to set file properties.
        :param metadata:
            Name-value pairs associated with the file as metadata.
        :type metadata: a dict mapping str to str
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('content_length', content_length)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = { 'timeout': _int_to_str(timeout)}
        request.headers = {
             'x-ms-content-length': _to_str(content_length),
             'x-ms-type': 'file'
        }
        _add_metadata_headers(metadata, request)
        if content_settings is not None:
            request.headers.update(content_settings._to_headers())

        self._perform_request(request)

    def create_file_from_path(self, share_name, directory_name, file_name, 
                           local_file_path, content_settings=None,
                           metadata=None, validate_content=False, progress_callback=None,
                           max_connections=2, timeout=None):
        '''
        Creates a new azure file from a local file path, or updates the content of an
        existing file, with automatic chunking and progress notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file to create or update.
        :param str local_file_path:
            Path of the local file to upload as the file content.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used for setting file properties.
        :param metadata:
            Name-value pairs associated with the file as metadata.
        :type metadata: a dict mapping str to str
        :param bool validate_content:
            If true, calculates an MD5 hash for each range of the file. The storage 
            service checks the hash of the content that has arrived with the hash 
            that was sent. This is primarily valuable for detecting bitflips on 
            the wire if using http instead of https as https (the default) will 
            already validate. Note that this MD5 hash is not stored with the 
            file.
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far and total is the
            size of the file, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('local_file_path', local_file_path)

        count = path.getsize(local_file_path)
        with open(local_file_path, 'rb') as stream:
            self.create_file_from_stream(
                share_name, directory_name, file_name, stream,
                count, content_settings, metadata, validate_content, progress_callback,
                max_connections, timeout)

    def create_file_from_text(self, share_name, directory_name, file_name, 
                           text, encoding='utf-8', content_settings=None,
                           metadata=None, validate_content=False, timeout=None):
        '''
        Creates a new file from str/unicode, or updates the content of an
        existing file, with automatic chunking and progress notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file to create or update.
        :param str text:
            Text to upload to the file.
        :param str encoding:
            Python encoding to use to convert the text to bytes.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used to set file properties.
        :param metadata:
            Name-value pairs associated with the file as metadata.
        :type metadata: a dict mapping str to str
        :param bool validate_content:
            If true, calculates an MD5 hash for each range of the file. The storage 
            service checks the hash of the content that has arrived with the hash 
            that was sent. This is primarily valuable for detecting bitflips on 
            the wire if using http instead of https as https (the default) will 
            already validate. Note that this MD5 hash is not stored with the 
            file.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('text', text)

        if not isinstance(text, bytes):
            _validate_not_none('encoding', encoding)
            text = text.encode(encoding)

        self.create_file_from_bytes(
            share_name, directory_name, file_name, text, count=len(text), 
            content_settings=content_settings, metadata=metadata, 
            validate_content=validate_content, timeout=timeout)

    def create_file_from_bytes(
        self, share_name, directory_name, file_name, file,
        index=0, count=None, content_settings=None, metadata=None, 
        validate_content=False, progress_callback=None, max_connections=2, 
        timeout=None):
        '''
        Creates a new file from an array of bytes, or updates the content
        of an existing file, with automatic chunking and progress
        notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file to create or update.
        :param str file:
            Content of file as an array of bytes.
        :param int index:
            Start index in the array of bytes.
        :param int count:
            Number of bytes to upload. Set to None or negative value to upload
            all bytes starting from index.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used to set file properties.
        :param metadata:
            Name-value pairs associated with the file as metadata.
        :type metadata: a dict mapping str to str
        :param bool validate_content:
            If true, calculates an MD5 hash for each range of the file. The storage 
            service checks the hash of the content that has arrived with the hash 
            that was sent. This is primarily valuable for detecting bitflips on 
            the wire if using http instead of https as https (the default) will 
            already validate. Note that this MD5 hash is not stored with the 
            file.
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far and total is the
            size of the file, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('file', file)
        _validate_type_bytes('file', file)

        if index < 0:
            raise TypeError(_ERROR_VALUE_NEGATIVE.format('index'))

        if count is None or count < 0:
            count = len(file) - index

        stream = BytesIO(file)
        stream.seek(index)

        self.create_file_from_stream(
            share_name, directory_name, file_name, stream, count,
            content_settings, metadata, validate_content, progress_callback,
            max_connections, timeout)

    def create_file_from_stream(
        self, share_name, directory_name, file_name, stream, count,
        content_settings=None, metadata=None, validate_content=False, 
        progress_callback=None, max_connections=2, timeout=None):
        '''
        Creates a new file from a file/stream, or updates the content of an
        existing file, with automatic chunking and progress notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of file to create or update.
        :param io.IOBase stream:
            Opened file/stream to upload as the file content.
        :param int count:
            Number of bytes to read from the stream. This is required, a
            file cannot be created if the count is unknown.
        :param ~azure.storage.file.models.ContentSettings content_settings:
            ContentSettings object used to set file properties.
        :param metadata:
            Name-value pairs associated with the file as metadata.
        :type metadata: a dict mapping str to str
        :param bool validate_content:
            If true, calculates an MD5 hash for each range of the file. The storage 
            service checks the hash of the content that has arrived with the hash 
            that was sent. This is primarily valuable for detecting bitflips on 
            the wire if using http instead of https as https (the default) will 
            already validate. Note that this MD5 hash is not stored with the 
            file.
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far and total is the
            size of the file, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use. Note that parallel upload 
            requires the stream to be seekable.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('stream', stream)
        _validate_not_none('count', count)

        if count < 0:
            raise TypeError(_ERROR_VALUE_NEGATIVE.format('count'))

        self.create_file(
            share_name,
            directory_name,
            file_name,
            count,
            content_settings,
            metadata,
            timeout
        )

        _upload_file_chunks(
            self,
            share_name,
            directory_name,
            file_name,
            count,
            self.MAX_RANGE_SIZE,
            stream,
            max_connections,
            progress_callback,
            validate_content,
            timeout
        )

    def _get_file(self, share_name, directory_name, file_name,
                 start_range=None, end_range=None, validate_content=False, 
                 timeout=None, _context=None):
        '''
        Downloads a file's content, metadata, and properties. You can specify a
        range if you don't need to download the file in its entirety. If no range
        is specified, the full file will be downloaded.

        See get_file_to_* for high level functions that handle the download
        of large files with automatic chunking and progress notifications.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int start_range:
            Start of byte range to use for downloading a section of the file.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for downloading a section of the file.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            When this is set to True and specified together with the Range header, 
            the service returns the MD5 hash for the range, as long as the range 
            is less than or equal to 4 MB in size.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A File with content, properties, and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = { 'timeout': _int_to_str(timeout)}
        _validate_and_format_range_headers(
            request,
            start_range,
            end_range,
            start_range_required=False,
            end_range_required=False,
            check_content_md5=validate_content)

        return self._perform_request(request, _parse_file, 
                                     [file_name, validate_content],
                                     operation_context=_context)

    def get_file_to_path(self, share_name, directory_name, file_name, file_path,
                         open_mode='wb', start_range=None, end_range=None,
                         validate_content=False, progress_callback=None,
                         max_connections=2, timeout=None):
        '''
        Downloads a file to a file path, with automatic chunking and progress
        notifications. Returns an instance of File with properties and metadata.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param str file_path:
            Path of file to write to.
        :param str open_mode:
            Mode to use when opening the file. Note that specifying append only 
            open_mode prevents parallel download. So, max_connections must be set 
            to 1 if this open_mode is used.
        :param int start_range:
            Start of byte range to use for downloading a section of the file.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for downloading a section of the file.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            If set to true, validates an MD5 hash for each retrieved portion of 
            the file. This is primarily valuable for detecting bitflips on the wire 
            if using http instead of https as https (the default) will already 
            validate. Note that the service will only return transactional MD5s 
            for chunks 4MB or less so the first get request will be of size 
            self.MAX_CHUNK_GET_SIZE instead of self.MAX_SINGLE_GET_SIZE. If 
            self.MAX_CHUNK_GET_SIZE was set to greater than 4MB an error will be 
            thrown. As computing the MD5 takes processing time and more requests 
            will need to be done due to the reduced chunk size there may be some 
            increase in latency.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the file if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            If set to 2 or greater, an initial get will be done for the first 
            self.MAX_SINGLE_GET_SIZE bytes of the file. If this is the entire file, 
            the method returns at this point. If it is not, it will download the 
            remaining data parallel using the number of threads equal to 
            max_connections. Each chunk will be of size self.MAX_CHUNK_GET_SIZE.
            If set to 1, a single large get request will be done. This is not 
            generally recommended but available if very few threads should be 
            used, network requests are very expensive, or a non-seekable stream 
            prevents parallel download. This may also be valuable if the file is 
            being concurrently modified to enforce atomicity or if many files are 
            expected to be empty as an extra request is required for empty files 
            if max_connections is greater than 1.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A File with properties and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('file_path', file_path)
        _validate_not_none('open_mode', open_mode)

        if max_connections > 1 and 'a' in open_mode:
            raise ValueError(_ERROR_PARALLEL_NOT_SEEKABLE)

        with open(file_path, open_mode) as stream:
            file = self.get_file_to_stream(
                share_name, directory_name, file_name, stream,
                start_range, end_range, validate_content,
                progress_callback, max_connections, timeout)

        return file

    def get_file_to_stream(
        self, share_name, directory_name, file_name, stream,
        start_range=None, end_range=None, validate_content=False,
        progress_callback=None, max_connections=2, timeout=None):
        '''
        Downloads a file to a stream, with automatic chunking and progress
        notifications. Returns an instance of :class:`File` with properties
        and metadata.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param io.IOBase stream:
            Opened file/stream to write to.
        :param int start_range:
            Start of byte range to use for downloading a section of the file.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for downloading a section of the file.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            If set to true, validates an MD5 hash for each retrieved portion of 
            the file. This is primarily valuable for detecting bitflips on the wire 
            if using http instead of https as https (the default) will already 
            validate. Note that the service will only return transactional MD5s 
            for chunks 4MB or less so the first get request will be of size 
            self.MAX_CHUNK_GET_SIZE instead of self.MAX_SINGLE_GET_SIZE. If 
            self.MAX_CHUNK_GET_SIZE was set to greater than 4MB an error will be 
            thrown. As computing the MD5 takes processing time and more requests 
            will need to be done due to the reduced chunk size there may be some 
            increase in latency.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the file if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            If set to 2 or greater, an initial get will be done for the first 
            self.MAX_SINGLE_GET_SIZE bytes of the file. If this is the entire file, 
            the method returns at this point. If it is not, it will download the 
            remaining data parallel using the number of threads equal to 
            max_connections. Each chunk will be of size self.MAX_CHUNK_GET_SIZE.
            If set to 1, a single large get request will be done. This is not 
            generally recommended but available if very few threads should be 
            used, network requests are very expensive, or a non-seekable stream 
            prevents parallel download. This may also be valuable if the file is 
            being concurrently modified to enforce atomicity or if many files are 
            expected to be empty as an extra request is required for empty files 
            if max_connections is greater than 1.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A File with properties and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('stream', stream)

        # If the user explicitly sets max_connections to 1, do a single shot download
        if max_connections == 1:
            file = self._get_file(share_name,
                                  directory_name,
                                  file_name,
                                  start_range=start_range,
                                  end_range=end_range,
                                  validate_content=validate_content,
                                  timeout=timeout)

            # Set the download size
            download_size = file.properties.content_length

        # If max_connections is greater than 1, do the first get to establish the 
        # size of the file and get the first segment of data
        else:       
            if sys.version_info >= (3,) and not stream.seekable():
                raise ValueError(_ERROR_PARALLEL_NOT_SEEKABLE)
                
            # The service only provides transactional MD5s for chunks under 4MB.           
            # If validate_content is on, get only self.MAX_CHUNK_GET_SIZE for the first 
            # chunk so a transactional MD5 can be retrieved.
            first_get_size = self.MAX_SINGLE_GET_SIZE if not validate_content else self.MAX_CHUNK_GET_SIZE

            initial_request_start = start_range if start_range else 0

            if end_range and end_range - start_range < first_get_size:
                initial_request_end = end_range
            else:
                initial_request_end = initial_request_start + first_get_size - 1

            # Send a context object to make sure we always retry to the initial location
            operation_context = _OperationContext(location_lock=True)
            try:
                file = self._get_file(share_name,
                                      directory_name,
                                      file_name,
                                      start_range=initial_request_start,
                                      end_range=initial_request_end,
                                      validate_content=validate_content,
                                      timeout=timeout,
                                      _context=operation_context)

                # Parse the total file size and adjust the download size if ranges 
                # were specified
                file_size = _parse_length_from_content_range(file.properties.content_range)
                if end_range:
                    # Use the end_range unless it is over the end of the file
                    download_size = min(file_size, end_range - start_range + 1)
                elif start_range:
                    download_size = file_size - start_range
                else:
                    download_size = file_size
            except AzureHttpError as ex:
                if not start_range and ex.status_code == 416:
                    # Get range will fail on an empty file. If the user did not 
                    # request a range, do a regular get request in order to get 
                    # any properties.
                    file = self._get_file(share_name,
                                          directory_name,
                                          file_name,
                                          validate_content=validate_content,
                                          timeout=timeout,
                                          _context=operation_context)

                    # Set the download size to empty
                    download_size = 0
                else:
                    raise ex

        # Mark the first progress chunk. If the file is small or this is a single 
        # shot download, this is the only call
        if progress_callback:
            progress_callback(file.properties.content_length, download_size)

        # Write the content to the user stream  
        # Clear file content since output has been written to user stream   
        if file.content is not None:
            stream.write(file.content)
            file.content = None

        # If the file is small or single shot download was used, the download is 
        # complete at this point. If file size is large, use parallel download.
        if file.properties.content_length != download_size:       
            # At this point would like to lock on something like the etag so that 
            # if the file is modified, we dont get a corrupted download. However, 
            # this feature is not yet available on the file service.
            
            end_file = file_size
            if end_range:
                # Use the end_range unless it is over the end of the file
                end_file = min(file_size, end_range + 1)
               
            _download_file_chunks(
                self,
                share_name,
                directory_name,
                file_name,
                download_size,
                self.MAX_CHUNK_GET_SIZE,
                first_get_size,
                initial_request_end + 1, # start where the first download ended
                end_file,
                stream,
                max_connections,
                progress_callback,
                validate_content,
                timeout,
                operation_context,
            )

            # Set the content length to the download size instead of the size of 
            # the last range
            file.properties.content_length = download_size

            # Overwrite the content range to the user requested range
            file.properties.content_range = 'bytes {0}-{1}/{2}'.format(start_range, end_range, file_size)

            # Overwrite the content MD5 as it is the MD5 for the last range instead 
            # of the stored MD5
            # TODO: Set to the stored MD5 when the service returns this
            file.properties.content_md5 = None

        return file

    def get_file_to_bytes(self, share_name, directory_name, file_name, 
                          start_range=None, end_range=None, validate_content=False,
                          progress_callback=None, max_connections=2, timeout=None):
        '''
        Downloads a file as an array of bytes, with automatic chunking and
        progress notifications. Returns an instance of :class:`File` with
        properties, metadata, and content.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int start_range:
            Start of byte range to use for downloading a section of the file.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for downloading a section of the file.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            If set to true, validates an MD5 hash for each retrieved portion of 
            the file. This is primarily valuable for detecting bitflips on the wire 
            if using http instead of https as https (the default) will already 
            validate. Note that the service will only return transactional MD5s 
            for chunks 4MB or less so the first get request will be of size 
            self.MAX_CHUNK_GET_SIZE instead of self.MAX_SINGLE_GET_SIZE. If 
            self.MAX_CHUNK_GET_SIZE was set to greater than 4MB an error will be 
            thrown. As computing the MD5 takes processing time and more requests 
            will need to be done due to the reduced chunk size there may be some 
            increase in latency.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the file if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            If set to 2 or greater, an initial get will be done for the first 
            self.MAX_SINGLE_GET_SIZE bytes of the file. If this is the entire file, 
            the method returns at this point. If it is not, it will download the 
            remaining data parallel using the number of threads equal to 
            max_connections. Each chunk will be of size self.MAX_CHUNK_GET_SIZE.
            If set to 1, a single large get request will be done. This is not 
            generally recommended but available if very few threads should be 
            used, network requests are very expensive, or a non-seekable stream 
            prevents parallel download. This may also be valuable if the file is 
            being concurrently modified to enforce atomicity or if many files are 
            expected to be empty as an extra request is required for empty files 
            if max_connections is greater than 1.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A File with properties, content, and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)

        stream = BytesIO()
        file = self.get_file_to_stream(
            share_name,
            directory_name,
            file_name,
            stream,
            start_range,
            end_range,
            validate_content,
            progress_callback,
            max_connections,
            timeout)

        file.content = stream.getvalue()
        return file

    def get_file_to_text(
        self, share_name, directory_name, file_name, encoding='utf-8',
        start_range=None, end_range=None, validate_content=False,
        progress_callback=None, max_connections=2, timeout=None):
        '''
        Downloads a file as unicode text, with automatic chunking and progress
        notifications. Returns an instance of :class:`File` with properties,
        metadata, and content.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param str encoding:
            Python encoding to use when decoding the file data.
        :param int start_range:
            Start of byte range to use for downloading a section of the file.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for downloading a section of the file.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            If set to true, validates an MD5 hash for each retrieved portion of 
            the file. This is primarily valuable for detecting bitflips on the wire 
            if using http instead of https as https (the default) will already 
            validate. Note that the service will only return transactional MD5s 
            for chunks 4MB or less so the first get request will be of size 
            self.MAX_CHUNK_GET_SIZE instead of self.MAX_SINGLE_GET_SIZE. If 
            self.MAX_CHUNK_GET_SIZE was set to greater than 4MB an error will be 
            thrown. As computing the MD5 takes processing time and more requests 
            will need to be done due to the reduced chunk size there may be some 
            increase in latency.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the file if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            If set to 2 or greater, an initial get will be done for the first 
            self.MAX_SINGLE_GET_SIZE bytes of the file. If this is the entire file, 
            the method returns at this point. If it is not, it will download the 
            remaining data parallel using the number of threads equal to 
            max_connections. Each chunk will be of size self.MAX_CHUNK_GET_SIZE.
            If set to 1, a single large get request will be done. This is not 
            generally recommended but available if very few threads should be 
            used, network requests are very expensive, or a non-seekable stream 
            prevents parallel download. This may also be valuable if the file is 
            being concurrently modified to enforce atomicity or if many files are 
            expected to be empty as an extra request is required for empty files 
            if max_connections is greater than 1.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A File with properties, content, and metadata.
        :rtype: :class:`~azure.storage.file.models.File`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('encoding', encoding)

        file = self.get_file_to_bytes(
            share_name,
            directory_name,
            file_name,
            start_range,
            end_range,
            validate_content,
            progress_callback,
            max_connections,
            timeout)

        file.content = file.content.decode(encoding)
        return file

    def update_range(self, share_name, directory_name, file_name, data, 
                     start_range, end_range, validate_content=False, timeout=None):
        '''
        Writes the bytes specified by the request body into the specified range.
         
        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param bytes data:
            Content of the range.
        :param int start_range:
            Start of byte range to use for updating a section of the file.
            The range can be up to 4 MB in size.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for updating a section of the file.
            The range can be up to 4 MB in size.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param bool validate_content:
            If true, calculates an MD5 hash of the page content. The storage 
            service checks the hash of the content that has arrived
            with the hash that was sent. This is primarily valuable for detecting 
            bitflips on the wire if using http instead of https as https (the default) 
            will already validate. Note that this MD5 hash is not stored with the 
            file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        _validate_not_none('data', data)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'range',
             'timeout': _int_to_str(timeout),
        }
        request.headers = {
             'x-ms-write': 'update',
        }
        _validate_and_format_range_headers(
            request, start_range, end_range)
        request.body = _get_data_bytes_only('data', data)

        if validate_content:
            computed_md5 = _get_content_md5(request.body)
            request.headers['Content-MD5'] = _to_str(computed_md5)

        self._perform_request(request)

    def clear_range(self, share_name, directory_name, file_name, start_range,
                    end_range, timeout=None):
        '''
        Clears the specified range and releases the space used in storage for 
        that range.
         
        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int start_range:
            Start of byte range to use for clearing a section of the file.
            The range can be up to 4 MB in size.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            End of byte range to use for clearing a section of the file.
            The range can be up to 4 MB in size.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'range',
             'timeout': _int_to_str(timeout),
        }
        request.headers = {
             'Content-Length': '0',
             'x-ms-write': 'clear',
        }
        _validate_and_format_range_headers(
            request, start_range, end_range)

        self._perform_request(request)

    def list_ranges(self, share_name, directory_name, file_name,
                    start_range=None, end_range=None, timeout=None):
        '''
        Retrieves the valid ranges for a file.

        :param str share_name:
            Name of existing share.
        :param str directory_name:
            The path to the directory.
        :param str file_name:
            Name of existing file.
        :param int start_range:
            Specifies the start offset of bytes over which to list ranges.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int end_range:
            Specifies the end offset of bytes over which to list ranges.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of file.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :returns: a list of valid ranges
        :rtype: a list of :class:`.FileRange`
        '''
        _validate_not_none('share_name', share_name)
        _validate_not_none('file_name', file_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host_locations = self._get_host_locations()
        request.path = _get_path(share_name, directory_name, file_name)
        request.query = {
             'comp': 'rangelist',
             'timeout': _int_to_str(timeout),
        }
        if start_range is not None:
            _validate_and_format_range_headers(
                request,
                start_range,
                end_range,
                start_range_required=False,
                end_range_required=False)

        return self._perform_request(request, _convert_xml_to_ranges)