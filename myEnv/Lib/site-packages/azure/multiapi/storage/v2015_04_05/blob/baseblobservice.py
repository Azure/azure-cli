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
    _ERROR_PARALLEL_NOT_SEEKABLE
)
from ._error import (
    _ERROR_INVALID_LEASE_DURATION,
    _ERROR_INVALID_LEASE_BREAK_PERIOD,
)
from .._common_conversion import (
    _int_to_str,
    _to_str,
    _datetime_to_utc_string,
)
from abc import ABCMeta
from .._serialization import (
    _get_request_body,
    _convert_signed_identifiers_to_xml,
    _convert_service_properties_to_xml,
)
from .._http import HTTPRequest
from ._chunking import _download_blob_chunks
from ..models import (
    Services,
    ListGenerator,
)
from .models import (
    Blob,
    BlobProperties,
    _LeaseActions,
    ContainerPermissions,
    BlobPermissions,
    Container,
    ContainerProperties,
)
from .._auth import (
    _StorageSASAuthentication,
    _StorageSharedKeyAuthentication,
    _StorageNoAuthentication,
)
from .._connection import _ServiceParameters
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
)
from .._deserialization import (
    _convert_xml_to_service_properties,
    _get_download_size,
    _parse_metadata,
    _parse_properties,
)
from ._serialization import (
    _get_path,
    _validate_and_format_range_headers,
)
from ._deserialization import (
    _convert_xml_to_containers,
    _parse_blob,
    _convert_xml_to_blob_list,
    _parse_container,
    _parse_snapshot_blob,
    _parse_lease_time,
    _parse_lease_id,
    _convert_xml_to_signed_identifiers_and_access,
    _parse_base_properties,
)
from ..sharedaccesssignature import (
    SharedAccessSignature,
)
from ..storageclient import StorageClient
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO

class BaseBlobService(StorageClient):

    '''
    This is the main class managing Blob resources.

    The Blob service stores text and binary data as blobs in the cloud.
    The Blob service offers the following three resources: the storage account,
    containers, and blobs. Within your storage account, containers provide a
    way to organize sets of blobs. For more information please see:
    https://msdn.microsoft.com/en-us/library/azure/ee691964.aspx
    '''

    __metaclass__ = ABCMeta
    MAX_SINGLE_GET_SIZE = 64 * 1024 * 1024
    MAX_CHUNK_GET_SIZE = 4 * 1024 * 1024

    def __init__(self, account_name=None, account_key=None, sas_token=None, 
                 is_emulated=False, protocol=DEFAULT_PROTOCOL, endpoint_suffix=SERVICE_HOST_BASE,
                 custom_domain=None, request_session=None, connection_string=None):
        '''
        :param str account_name:
            The storage account name. This is used to authenticate requests 
            signed with an account key and to construct the storage endpoint. It 
            is required unless a connection string is given, or if a custom 
            domain is used with anonymous authentication.
        :param str account_key:
            The storage account key. This is used for shared key authentication. 
            If neither account key or sas token is specified, anonymous access 
            will be used.
        :param str sas_token:
             A shared access signature token to use to authenticate requests 
             instead of the account key. If account key and sas token are both 
             specified, account key will be used to sign. If neither are 
             specified, anonymous access will be used.
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
        :param str custom_domain:
            The custom domain to use. This can be set in the Azure Portal. For 
            example, 'www.mydomain.com'.
        :param requests.Session request_session:
            The session object to use for http requests.
        :param str connection_string:
            If specified, this will override all other parameters besides 
            request session. See
            http://azure.microsoft.com/en-us/documentation/articles/storage-configure-connection-string/
            for the connection string format.
        '''
        service_params = _ServiceParameters.get_service_parameters(
            'blob',
            account_name=account_name, 
            account_key=account_key,
            sas_token=sas_token, 
            is_emulated=is_emulated,
            protocol=protocol, 
            endpoint_suffix=endpoint_suffix,
            custom_domain=custom_domain,
            request_session=request_session,
            connection_string=connection_string)

        super(BaseBlobService, self).__init__(service_params)

        if self.account_key:
            self.authentication = _StorageSharedKeyAuthentication(
                self.account_name,
                self.account_key,
            )
        elif self.sas_token:
            self.authentication = _StorageSASAuthentication(self.sas_token)
        else:
            self.authentication = _StorageNoAuthentication()

    def make_blob_url(self, container_name, blob_name, protocol=None, sas_token=None):
        '''
        Creates the url to access a blob.

        :param str container_name:
            Name of container.
        :param str blob_name:
            Name of blob.
        :param str protocol:
            Protocol to use: 'http' or 'https'. If not specified, uses the
            protocol specified when BaseBlobService was initialized.
        :param str sas_token:
            Shared access signature token created with
            generate_shared_access_signature.
        :return: blob access URL.
        :rtype: str
        '''

        url = '{}://{}/{}/{}'.format(
            protocol or self.protocol,
            self.primary_endpoint,
            container_name,
            blob_name,
        )

        if sas_token:
            url += '?' + sas_token

        return url

    def generate_account_shared_access_signature(self, resource_types, permission, 
                                        expiry, start=None, ip=None, protocol=None):
        '''
        Generates a shared access signature for the blob service.
        Use the returned signature with the sas_token parameter of any BlobService.

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
        return sas.generate_account(Services.BLOB, resource_types, permission, 
                                    expiry, start=start, ip=ip, protocol=protocol)

    def generate_container_shared_access_signature(self, container_name, 
                        permission=None, expiry=None, 
                        start=None, id=None, ip=None, protocol=None,
                        cache_control=None, content_disposition=None,
                        content_encoding=None, content_language=None,
                        content_type=None):
        '''
        Generates a shared access signature for the container.
        Use the returned signature with the sas_token parameter of any BlobService.

        :param str container_name:
            Name of container.
        :param ContainerPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, write, delete, list.
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
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
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
        _validate_not_none('container_name', container_name)
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_container(
            container_name,
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

    def generate_blob_shared_access_signature(
        self, container_name, blob_name, permission=None, 
        expiry=None, start=None, id=None, ip=None, protocol=None,
        cache_control=None, content_disposition=None,
        content_encoding=None, content_language=None,
        content_type=None):
        '''
        Generates a shared access signature for the blob.
        Use the returned signature with the sas_token parameter of any BlobService.

        :param str container_name:
            Name of container.
        :param str blob_name:
            Name of blob.
        :param BlobPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, write, delete, list.
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
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
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
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('self.account_name', self.account_name)
        _validate_not_none('self.account_key', self.account_key)

        sas = SharedAccessSignature(self.account_name, self.account_key)
        return sas.generate_blob(
            container_name,
            blob_name,
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

    def list_containers(self, prefix=None, num_results=None, include_metadata=False, 
                        marker=None, timeout=None):
        '''
        Returns a generator to list the containers under the specified account.
        The generator will lazily follow the continuation tokens returned by
        the service and stop when all containers have been returned or num_results is reached.

        If num_results is specified and the account has more than that number of 
        containers, the generator will have a populated next_marker field once it 
        finishes. This marker can be used to create a new generator if more 
        results are desired.

        :param str prefix:
            Filters the results to return only containers whose names
            begin with the specified prefix.
        :param int num_results:
            Specifies the maximum number of containers to return. A single list
            request may return up to 1000 contianers and potentially a continuation
            token which should be followed to get additional resutls.
        :param bool include_metadata:
            Specifies that container metadata be returned in the response.
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
        kwargs = {'prefix': prefix, 'marker': marker, 'max_results': num_results, 
                'include': include, 'timeout': timeout}
        resp = self._list_containers(**kwargs)

        return ListGenerator(resp, self._list_containers, (), kwargs)


    def _list_containers(self, prefix=None, marker=None, max_results=None, 
                         include=None, timeout=None):
        '''
        Returns a list of the containers under the specified account.

        :param str prefix:
            Filters the results to return only containers whose names
            begin with the specified prefix.
        :param str marker:
            A string value that identifies the portion of the list
            to be returned with the next list operation. The operation returns
            a next_marker value within the response body if the list returned was
            not complete. The marker value may then be used in a subsequent
            call to request the next set of list items. The marker value is
            opaque to the client.
        :param int max_results:
            Specifies the maximum number of containers to return. A single list
            request may return up to 1000 contianers and potentially a continuation
            token which should be followed to get additional resutls.
        :param str include:
            Include this parameter to specify that the container's
            metadata be returned as part of the response body. set this
            parameter to string 'metadata' to get container's metadata.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path() 
        request.query = [
            ('comp', 'list'),
            ('prefix', _to_str(prefix)),
            ('marker', _to_str(marker)),
            ('maxresults', _int_to_str(max_results)),
            ('include', _to_str(include)),
            ('timeout', _int_to_str(timeout))
        ]

        response = self._perform_request(request)
        return _convert_xml_to_containers(response)

    def create_container(self, container_name, metadata=None,
                         public_access=None, fail_on_exist=False, timeout=None):
        '''
        Creates a new container under the specified account. If the container
        with the same name already exists, the operation fails if
        fail_on_exist is True.

        :param str container_name:
            Name of container to create.
        :param metadata:
            A dict with name_value pairs to associate with the
            container as metadata. Example:{'Category':'test'}
        :type metadata: a dict mapping str to str
        :param public_access:
            Possible values include: container, blob.
        :type public_access:
            One of the values listed in the :class:`~azure.storage.blob.models.PublicAccess` enum.
        :param bool fail_on_exist:
            Specify whether to throw an exception when the container exists.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if container is created, False if container already exists.
        :rtype: bool
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('timeout', _int_to_str(timeout)),]
        request.headers = [
            ('x-ms-meta-name-values', metadata),
            ('x-ms-blob-public-access', _to_str(public_access))
        ]

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

    def get_container_properties(self, container_name, lease_id=None, timeout=None):
        '''
        Returns all user-defined metadata and system properties for the specified
        container. The data returned does not include the container's list of blobs.

        :param str container_name:
            Name of existing container.
        :param str lease_id:
            If specified, get_container_properties only succeeds if the
            container's lease is active and matches this ID.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: properties for the specified container within a container object.
        :rtype: :class:`~azure.storage.blob.models.Container`
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [('x-ms-lease-id', _to_str(lease_id))]

        response = self._perform_request(request)
        return _parse_container(container_name, response)

    def get_container_metadata(self, container_name, lease_id=None, timeout=None):
        '''
        Returns all user-defined metadata for the specified container.

        :param str container_name:
            Name of existing container.
        :param str lease_id:
            If specified, get_container_metadata only succeeds if the
            container's lease is active and matches this ID.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            A dictionary representing the container metadata name, value pairs.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'metadata'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [('x-ms-lease-id', _to_str(lease_id))]

        response = self._perform_request(request)
        return _parse_metadata(response)

    def set_container_metadata(self, container_name, metadata=None,
                               lease_id=None, if_modified_since=None, timeout=None):
        '''
        Sets one or more user-defined name-value pairs for the specified
        container. Each call to this operation replaces all existing metadata
        attached to the container. To remove all metadata from the container,
        call this operation with no metadata dict.

        :param str container_name:
            Name of existing container.
        :param metadata:
            A dict containing name-value pairs to associate with the container as 
            metadata. Example: {'category':'test'}
        :type metadata: a dict mapping str to str
        :param str lease_id:
            If specified, set_container_metadata only succeeds if the
            container's lease is active and matches this ID.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Container
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'metadata'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-meta-name-values', metadata),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('x-ms-lease-id', _to_str(lease_id)),
        ]

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def get_container_acl(self, container_name, lease_id=None, timeout=None):
        '''
        Gets the permissions for the specified container.
        The permissions indicate whether container data may be accessed publicly.

        :param str container_name:
            Name of existing container.
        :param lease_id:
            If specified, get_container_acl only succeeds if the
            container's lease is active and matches this ID.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A dictionary of access policies associated with the container.
        :rtype:
            dict of str to :class:`.AccessPolicy` and a public_access property
            if public access is turned on
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'acl'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [('x-ms-lease-id', _to_str(lease_id))]

        response = self._perform_request(request)
        return _convert_xml_to_signed_identifiers_and_access(response)

    def set_container_acl(self, container_name, signed_identifiers=None,
                          public_access=None, lease_id=None,
                          if_modified_since=None, if_unmodified_since=None, timeout=None):
        '''
        Sets the permissions for the specified container or stored access 
        policies that may be used with Shared Access Signatures. The permissions
        indicate whether blobs in a container may be accessed publicly.

        :param str container_name:
            Name of existing container.
        :param signed_identifiers:
            A dictionary of access policies to associate with the container. The 
            dictionary may contain up to 5 elements. An empty dictionary 
            will clear the access policies set on the service. 
        :type signed_identifiers: dict of str to :class:`.AccessPolicy`
        :param public_access:
            Possible values include: container, blob.
        :type public_access: 
            One of the values listed in the :class:`~azure.storage.blob.models.PublicAccess` enum.
        :param str lease_id:
            If specified, set_container_acl only succeeds if the
            container's lease is active and matches this ID.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Container
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'acl'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-blob-public-access', _to_str(public_access)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('x-ms-lease-id', _to_str(lease_id)),
        ]
        request.body = _get_request_body(
            _convert_signed_identifiers_to_xml(signed_identifiers))

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def delete_container(self, container_name, fail_not_exist=False,
                         lease_id=None, if_modified_since=None,
                         if_unmodified_since=None, timeout=None):
        '''
        Marks the specified container for deletion. The container and any blobs
        contained within it are later deleted during garbage collection.

        :param str container_name:
            Name of container to delete.
        :param bool fail_not_exist:
            Specify whether to throw an exception when the container doesn't
            exist.
        :param str lease_id:
            If specified, delete_container only succeeds if the
            container's lease is active and matches this ID.
            Required if the container has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: True if container is deleted, False container doesn't exist.
        :rtype: bool
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),          
        ]

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

    def _lease_container_impl(
        self, container_name, lease_action, lease_id, lease_duration,
        lease_break_period, proposed_lease_id, if_modified_since,
        if_unmodified_since, timeout):
        '''
        Establishes and manages a lock on a container for delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.
        The Lease Container operation can be called in one of five modes
            Acquire, to request a new lease
            Renew, to renew an existing lease
            Change, to change the ID of an existing lease
            Release, to free the lease if it is no longer needed so that another
                client may immediately acquire a lease against the container
            Break, to end the lease but ensure that another client cannot acquire
                a new lease until the current lease period has expired

        :param str container_name:
            Name of existing container.
        :param str lease_action:
            Possible _LeaseActions values: acquire|renew|release|break|change
        :param str lease_id:
            Required if the container has an active lease.
        :param int lease_duration:
            Specifies the duration of the lease, in seconds, or negative one
            (-1) for a lease that never expires. A non-infinite lease can be
            between 15 and 60 seconds. A lease duration cannot be changed
            using renew or change. For backwards compatibility, the default is
            60, and the value is only used on an acquire operation.
        :param int lease_break_period:
            For a break operation, this is the proposed duration of
            seconds that the lease should continue before it is broken, between
            0 and 60 seconds. This break period is only used if it is shorter
            than the time remaining on the lease. If longer, the time remaining
            on the lease is used. A new lease will not be available before the
            break period has expired, but the lease may be held for longer than
            the break period. If this header does not appear with a break
            operation, a fixed-duration lease breaks after the remaining lease
            period elapses, and an infinite lease breaks immediately.
        :param str proposed_lease_id:
            Optional for Acquire, required for Change. Proposed lease ID, in a
            GUID string format. The Blob service returns 400 (Invalid request)
            if the proposed lease ID is not in the correct format.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            Response headers returned from the service call.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('lease_action', lease_action)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'lease'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-lease-action', _to_str(lease_action)),
            ('x-ms-lease-duration', _to_str(lease_duration)),
            ('x-ms-lease-break-period', _to_str(lease_break_period)),
            ('x-ms-proposed-lease-id', _to_str(proposed_lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
        ]

        return self._perform_request(request)

    def acquire_container_lease(
        self, container_name, lease_duration=-1, proposed_lease_id=None,
        if_modified_since=None, if_unmodified_since=None, timeout=None):
        '''
        Acquires a lock on a container for delete operations.
        The lock duration can be 15 to 60 seconds or infinite.

        :param str container_name:
            Name of existing container.
        :param int lease_duration:
            Specifies the duration of the lease, in seconds, or negative one
            (-1) for a lease that never expires. A non-infinite lease can be
            between 15 and 60 seconds. A lease duration cannot be changed
            using renew or change. Default is -1 (infinite lease).
        :param str proposed_lease_id:
            Proposed lease ID, in a GUID string format. The Blob service returns
            400 (Invalid request) if the proposed lease ID is not in the correct format.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: the lease ID of the newly created lease.
        :return: str
        '''
        _validate_not_none('lease_duration', lease_duration)
        if lease_duration is not -1 and\
           (lease_duration < 15 or lease_duration > 60):
            raise ValueError(_ERROR_INVALID_LEASE_DURATION)

        response = self._lease_container_impl(container_name, 
                                          _LeaseActions.Acquire,
                                          None, # lease_id
                                          lease_duration,
                                          None, # lease_break_period
                                          proposed_lease_id,
                                          if_modified_since,
                                          if_unmodified_since,
                                          timeout)
        return _parse_lease_id(response)

    def renew_container_lease(
        self, container_name, lease_id, if_modified_since=None,
        if_unmodified_since=None, timeout=None):
        '''
        Renews a lock on a container for delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str lease_id:
            Lease ID for active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: the lease ID of the renewed lease.
        :return: str
        '''
        _validate_not_none('lease_id', lease_id)

        response =  self._lease_container_impl(container_name, 
                                          _LeaseActions.Renew,
                                          lease_id,
                                          None, # lease_duration
                                          None, # lease_break_period
                                          None, # proposed_lease_id
                                          if_modified_since,
                                          if_unmodified_since,
                                          timeout)
        return _parse_lease_id(response)

    def release_container_lease(
        self, container_name, lease_id, if_modified_since=None,
        if_unmodified_since=None, timeout=None):
        '''
        Releases a lock on a container for delete operations, to free the
        lease if it is no longer needed so that another client may
        immediately acquire a lease against the container. The lock duration
        can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str lease_id:
            Lease ID for active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('lease_id', lease_id)

        self._lease_container_impl(container_name, 
                                    _LeaseActions.Release,
                                    lease_id,
                                    None, # lease_duration
                                    None, # lease_break_period
                                    None, # proposed_lease_id
                                    if_modified_since,
                                    if_unmodified_since,
                                    timeout)

    def break_container_lease(
        self, container_name, lease_break_period=None,
        if_modified_since=None, if_unmodified_since=None, timeout=None):
        '''
        Breaks a lock on a container for delete operations.
        Use to end the lease but ensure that another client cannot
        acquire a new lease until the current lease period has expired.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param int lease_break_period:
            This is the proposed duration of seconds that the lease
            should continue before it is broken, between 0 and 60 seconds. This
            break period is only used if it is shorter than the time remaining
            on the lease. If longer, the time remaining on the lease is used.
            A new lease will not be available before the break period has
            expired, but the lease may be held for longer than the break
            period. If this header does not appear with a break
            operation, a fixed-duration lease breaks after the remaining lease
            period elapses, and an infinite lease breaks immediately.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: Approximate time remaining in the lease period, in seconds.
        :return: int
        '''
        if (lease_break_period is not None) and (lease_break_period < 0 or lease_break_period > 60):
            raise ValueError(_ERROR_INVALID_LEASE_BREAK_PERIOD)
        
        response = self._lease_container_impl(container_name, 
                                          _LeaseActions.Break,
                                          None, # lease_id
                                          None, # lease_duration
                                          lease_break_period,
                                          None, # proposed_lease_id
                                          if_modified_since,
                                          if_unmodified_since,
                                          timeout)
        return _parse_lease_time(response)

    def change_container_lease(
        self, container_name, lease_id, proposed_lease_id,
        if_modified_since=None, if_unmodified_since=None, timeout=None):
        '''
        Changes the lease ID for a lock on a container for delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str lease_id:
            Lease ID for active lease.
        :param str proposed_lease_id:
            Proposed lease ID, in a GUID string format. The Blob service returns 400
            (Invalid request) if the proposed lease ID is not in the correct format.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('lease_id', lease_id)

        self._lease_container_impl(container_name, 
                                    _LeaseActions.Change,
                                    lease_id,
                                    None, # lease_duration
                                    None, # lease_break_period
                                    proposed_lease_id,
                                    if_modified_since,
                                    if_unmodified_since,
                                    timeout)

    def list_blobs(self, container_name, prefix=None, num_results=None, include=None, 
                   delimiter=None, marker=None, timeout=None):
        '''
        Returns a generator to list the blobs under the specified container.
        The generator will lazily follow the continuation tokens returned by
        the service and stop when all blobs have been returned or num_results is reached.

        If num_results is specified and the account has more than that number of 
        blobs, the generator will have a populated next_marker field once it 
        finishes. This marker can be used to create a new generator if more 
        results are desired.

        :param str container_name:
            Name of existing container.
        :param str prefix:
            Filters the results to return only blobs whose names
            begin with the specified prefix.
        :param int num_results:
            Specifies the maximum number of blobs to return,
            including all :class:`BlobPrefix` elements. If the request does not specify
            num_results or specifies a value greater than 5,000, the server will
            return up to 5,000 items. Setting num_results to a value less than
            or equal to zero results in error response code 400 (Bad Request).
        :param ~azure.storage.blob.models.Include include:
            Specifies one or more additional datasets to include in the response.
        :param str delimiter:
            When the request includes this parameter, the operation
            returns a :class:`~azure.storage.blob.models.BlobPrefix` element in the
            result list that acts as a placeholder for all blobs whose names begin
            with the same substring up to the appearance of the delimiter character.
            The delimiter may be a single character or a string.
        :param str marker:
            An opaque continuation token. This value can be retrieved from the 
            next_marker field of a previous generator object if num_results was 
            specified and that generator has finished enumerating results. If 
            specified, this generator will begin returning results from the point 
            where the previous generator stopped.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        args = (container_name,)
        kwargs = {'prefix': prefix, 'marker': marker, 'max_results': num_results, 
                'include': include, 'delimiter': delimiter, 'timeout': timeout}
        resp = self._list_blobs(*args, **kwargs)

        return ListGenerator(resp, self._list_blobs, args, kwargs)

    def _list_blobs(self, container_name, prefix=None, marker=None,
                   max_results=None, include=None, delimiter=None, timeout=None):
        '''
        Returns the list of blobs under the specified container.

        :param str container_name:
            Name of existing container.
        :parm str prefix:
            Filters the results to return only blobs whose names
            begin with the specified prefix.
        :param str marker:
            A string value that identifies the portion of the list
            to be returned with the next list operation. The operation returns
            a next_marker value within the response body if the list returned was
            not complete. The marker value may then be used in a subsequent
            call to request the next set of list items. The marker value is
            opaque to the client.
        :param int max_results:
            Specifies the maximum number of blobs to return,
            including all :class:`BlobPrefix` elements. If the request does not specify
            max_results or specifies a value greater than 5,000, the server will
            return up to 5,000 items. Setting max_results to a value less than
            or equal to zero results in error response code 400 (Bad Request).
        :param str include:
            Specifies one or more datasets to include in the
            response. To specify more than one of these options on the URI,
            you must separate each option with a comma. Valid values are:
                snapshots:
                    Specifies that snapshots should be included in the
                    enumeration. Snapshots are listed from oldest to newest in
                    the response.
                metadata:
                    Specifies that blob metadata be returned in the response.
                uncommittedblobs:
                    Specifies that blobs for which blocks have been uploaded,
                    but which have not been committed using Put Block List
                    (REST API), be included in the response.
                copy:
                    Version 2012-02-12 and newer. Specifies that metadata
                    related to any current or previous Copy Blob operation
                    should be included in the response.
        :param str delimiter:
            When the request includes this parameter, the operation
            returns a :class:`BlobPrefix` element in the response body that acts as a
            placeholder for all blobs whose names begin with the same
            substring up to the appearance of the delimiter character. The
            delimiter may be a single character or a string.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('container_name', container_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name)
        request.query = [
            ('restype', 'container'),
            ('comp', 'list'),
            ('prefix', _to_str(prefix)),
            ('delimiter', _to_str(delimiter)),
            ('marker', _to_str(marker)),
            ('maxresults', _int_to_str(max_results)),
            ('include', _to_str(include)),
            ('timeout', _int_to_str(timeout)),
        ]

        response = self._perform_request(request)
        return _convert_xml_to_blob_list(response)

    def set_blob_service_properties(
        self, logging=None, hour_metrics=None, minute_metrics=None,
        cors=None, target_version=None, timeout=None):
        '''
        Sets the properties of a storage account's Blob service, including
        Azure Storage Analytics. If an element (ex Logging) is left as None, the 
        existing settings on the service for that functionality are preserved.

        :param Logging logging:
            Groups the Azure Analytics Logging settings.
        :param Metrics hour_metrics:
            The hour metrics settings provide a summary of request 
            statistics grouped by API in hourly aggregates for blobs.
        :param Metrics minute_metrics:
            The minute metrics settings provide request statistics 
            for each minute for blobs.
        :param cors:
            You can include up to five CorsRule elements in the 
            list. If an empty list is specified, all CORS rules will be deleted, 
            and CORS will be disabled for the service.
        :type cors: list of :class:`CorsRule`
        :param string target_version:
            Indicates the default version to use for requests if an incoming 
            request's version is not specified. 
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path() 
        request.query = [
            ('restype', 'service'),
            ('comp', 'properties'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.body = _get_request_body(
            _convert_service_properties_to_xml(logging, hour_metrics, minute_metrics, cors, target_version))

        self._perform_request(request)

    def get_blob_service_properties(self, timeout=None):
        '''
        Gets the properties of a storage account's Blob service, including
        Azure Storage Analytics.

        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: The blob service properties.
        :rtype:
            :class:`~azure.storage.models.ServiceProperties` with an attached
            target_version property
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path() 
        request.query = [
            ('restype', 'service'),
            ('comp', 'properties'),
            ('timeout', _int_to_str(timeout)),
        ]

        response = self._perform_request(request)
        return _convert_xml_to_service_properties(response.body)

    def get_blob_properties(
        self, container_name, blob_name, snapshot=None, lease_id=None,
        if_modified_since=None, if_unmodified_since=None, if_match=None,
        if_none_match=None, timeout=None):
        '''
        Returns all user-defined metadata, standard HTTP properties, and
        system properties for the blob. It does not return the content of the blob.
        Returns :class:`.Blob` with :class:`.BlobProperties` and a metadata dict.
        
        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: a blob object including properties and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'HEAD'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('snapshot', _to_str(snapshot)),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]

        response = self._perform_request(request)
        return _parse_blob(blob_name, snapshot, response)

    def set_blob_properties(
        self, container_name, blob_name, content_settings=None, lease_id=None,
        if_modified_since=None, if_unmodified_since=None, if_match=None,
        if_none_match=None, timeout=None):
        '''
        Sets system properties on the blob. If one property is set for the
        content_settings, all properties will be overriden.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set blob properties.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'properties'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers += [
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
            ('x-ms-lease-id', _to_str(lease_id))
        ]
        if content_settings is not None:
            request.headers += content_settings._to_headers()

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def exists(self, container_name, blob_name=None, snapshot=None, timeout=None):
        '''
        Returns a boolean indicating whether the container exists (if blob_name 
        is None), or otherwise a boolean indicating whether the blob exists.

        :param str container_name:
            Name of a container.
        :param str blob_name:
            Name of a blob. If None, the container will be checked for existence.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the snapshot.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A boolean indicating whether the resource exists.
        :rtype: bool
        '''
        _validate_not_none('container_name', container_name)
        try:
            if blob_name is None:
                self.get_container_properties(container_name, timeout=timeout)
            else:
                self.get_blob_properties(container_name, blob_name, snapshot=snapshot, timeout=timeout)
            return True
        except AzureHttpError as ex:
            _dont_fail_not_exist(ex)
            return False

    def _get_blob(
        self, container_name, blob_name, snapshot=None, start_range=None,
        end_range=None, range_get_content_md5=None, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
        '''
        Downloads a blob's content, metadata, and properties. You can also
        call this API to read a snapshot. You can specify a range if you don't
        need to download the blob in its entirety. If no range is specified,
        the full blob will be downloaded.

        See get_blob_to_* for high level functions that handle the download
        of large blobs with automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param int start_range:
            Start of byte range to use for downloading a section of the blob.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param int end_range:
            End of byte range to use for downloading a section of the blob.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param bool range_get_content_md5:
            When this header is set to True and specified together
            with the Range header, the service returns the MD5 hash for the
            range, as long as the range is less than or equal to 4 MB in size.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: A Blob with content, properties, and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('snapshot', _to_str(snapshot)),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]
        _validate_and_format_range_headers(
            request,
            start_range,
            end_range,
            start_range_required=False,
            end_range_required=False,
            check_content_md5=range_get_content_md5)

        response = self._perform_request(request, None)
        return _parse_blob(blob_name, snapshot, response)

    def get_blob_to_path(
        self, container_name, blob_name, file_path, open_mode='wb',
        snapshot=None, start_range=None, end_range=None,
        range_get_content_md5=None, progress_callback=None,
        max_connections=1, max_retries=5, retry_wait=1.0, lease_id=None,
        if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Downloads a blob to a file path, with automatic chunking and progress
        notifications. Returns an instance of :class:`Blob` with 
        properties and metadata.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str file_path:
            Path of file to write out to.
        :param str open_mode:
            Mode to use when opening the file.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param int start_range:
            Start of byte range to use for downloading a section of the blob.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param int end_range:
            End of byte range to use for downloading a section of the blob.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param bool range_get_content_md5:
            When this header is set to True and specified together
            with the Range header, the service returns the MD5 hash for the
            range, as long as the range is less than or equal to 4 MB in size.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the blob if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Set to 1 to download the blob sequentially.
            Set to 2 or greater if you want to download a blob larger than 64MB in chunks.
            If the blob size does not exceed 64MB it will be downloaded in one chunk.
        :param int max_retries:
            Number of times to retry download of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A Blob with properties and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('file_path', file_path)
        _validate_not_none('open_mode', open_mode)

        with open(file_path, open_mode) as stream:
            blob = self.get_blob_to_stream(
                container_name,
                blob_name,
                stream,
                snapshot,
                start_range,
                end_range,
                range_get_content_md5,
                progress_callback,
                max_connections,
                max_retries,
                retry_wait,
                lease_id,
                if_modified_since,
                if_unmodified_since,
                if_match,
                if_none_match,
                timeout)

        return blob

    def get_blob_to_stream(
        self, container_name, blob_name, stream, snapshot=None,
        start_range=None, end_range=None, range_get_content_md5=None,
        progress_callback=None, max_connections=1, max_retries=5,
        retry_wait=1.0, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):

        '''
        Downloads a blob to a stream, with automatic chunking and progress
        notifications. Returns an instance of :class:`Blob` with
        properties and metadata.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param io.IOBase stream:
            Opened stream to write to.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param int start_range:
            Start of byte range to use for downloading a section of the blob.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param int end_range:
            End of byte range to use for downloading a section of the blob.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param bool range_get_content_md5:
            When this header is set to True and specified together
            with the Range header, the service returns the MD5 hash for the
            range, as long as the range is less than or equal to 4 MB in size.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the blob if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Set to 1 to download the blob sequentially.
            Set to 2 or greater if you want to download a blob larger than 64MB in chunks.
            If the blob size does not exceed 64MB it will be downloaded in one chunk.
        :param int max_retries:
            Number of times to retry download of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A Blob with properties and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('stream', stream)

        if sys.version_info >= (3,) and max_connections > 1 and not stream.seekable():
            raise ValueError(_ERROR_PARALLEL_NOT_SEEKABLE)

        # Only get properties if parallelism will actually be used
        blob_size = None
        if max_connections > 1 and range_get_content_md5 is None:
            blob = self.get_blob_properties(container_name, blob_name, timeout=timeout)
            blob_size = blob.properties.content_length

            # If blob size is large, use parallel download
            if blob_size >= self.MAX_SINGLE_GET_SIZE:
                _download_blob_chunks(
                    self,
                    container_name,
                    blob_name,
                    blob_size,
                    self.MAX_CHUNK_GET_SIZE,
                    start_range,
                    end_range,
                    stream,
                    max_connections,
                    max_retries,
                    retry_wait,
                    progress_callback,
                    if_modified_since,
                    if_unmodified_since,
                    if_match,
                    if_none_match,
                    timeout,
                )
                return blob

        # If parallelism is off or the blob is small, do a single download
        download_size = _get_download_size(start_range, end_range, blob_size)
        if progress_callback:
            progress_callback(0, download_size)

        blob = self._get_blob(container_name,
                              blob_name,
                              snapshot,
                              start_range=start_range,
                              end_range=end_range,
                              range_get_content_md5=range_get_content_md5,
                              lease_id=lease_id,
                              if_modified_since=if_modified_since,
                              if_unmodified_since=if_unmodified_since,
                              if_match=if_match,
                              if_none_match=if_none_match,
                              timeout=timeout)

        if blob.content is not None:
            stream.write(blob.content)
    
        if progress_callback:
            download_size = len(blob.content)
            progress_callback(download_size, download_size)

        blob.content = None # Clear blob content since output has been written to user stream
        return blob
        
    def get_blob_to_bytes(
        self, container_name, blob_name, snapshot=None,
        start_range=None, end_range=None, range_get_content_md5=None,
        progress_callback=None, max_connections=1, max_retries=5,
        retry_wait=1.0, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None,
        timeout=None):
        '''
        Downloads a blob as an array of bytes, with automatic chunking and
        progress notifications. Returns an instance of :class:`Blob` with
        properties, metadata, and content.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param int start_range:
            Start of byte range to use for downloading a section of the blob.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param int end_range:
            End of byte range to use for downloading a section of the blob.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param bool range_get_content_md5:
            When this header is set to True and specified together
            with the Range header, the service returns the MD5 hash for the
            range, as long as the range is less than or equal to 4 MB in size.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the blob if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Set to 1 to download the blob sequentially.
            Set to 2 or greater if you want to download a blob larger than 64MB in chunks.
            If the blob size does not exceed 64MB it will be downloaded in one chunk.
        :param int max_retries:
            Number of times to retry download of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A Blob with content, properties, and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)

        stream = BytesIO()
        blob = self.get_blob_to_stream(
            container_name,
            blob_name,
            stream,
            snapshot,
            start_range,
            end_range,
            range_get_content_md5,
            progress_callback,
            max_connections,
            max_retries,
            retry_wait,
            lease_id,
            if_modified_since,
            if_unmodified_since,
            if_match,
            if_none_match,
            timeout)

        blob.content = stream.getvalue()
        return blob

    def get_blob_to_text(
        self, container_name, blob_name, encoding='utf-8', snapshot=None,
        start_range=None, end_range=None, range_get_content_md5=None,
        progress_callback=None, max_connections=1, max_retries=5,
        retry_wait=1.0, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None,
        timeout=None):
        '''
        Downloads a blob as unicode text, with automatic chunking and progress
        notifications. Returns an instance of :class:`Blob` with
        properties, metadata, and content.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str encoding:
            Python encoding to use when decoding the blob data.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve.
        :param int start_range:
            Start of byte range to use for downloading a section of the blob.
            If no end_range is given, all bytes after the start_range will be downloaded.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param int end_range:
            End of byte range to use for downloading a section of the blob.
            If end_range is given, start_range must be provided.
            The start_range and end_range params are inclusive.
            Ex: start_range=0, end_range=511 will download first 512 bytes of blob.
        :param bool range_get_content_md5:
            When this header is set to True and specified together
            with the Range header, the service returns the MD5 hash for the
            range, as long as the range is less than or equal to 4 MB in size.
        :param progress_callback:
            Callback for progress with signature function(current, total) 
            where current is the number of bytes transfered so far, and total is 
            the size of the blob if known.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Set to 1 to download the blob sequentially.
            Set to 2 or greater if you want to download a blob larger than 64MB in chunks.
            If the blob size does not exceed 64MB it will be downloaded in one chunk.
        :param int max_retries:
            Number of times to retry download of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        :return: A Blob with content, properties, and metadata.
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('encoding', encoding)

        blob = self.get_blob_to_bytes(container_name,
                                        blob_name,
                                        snapshot,
                                        start_range,
                                        end_range,
                                        range_get_content_md5,
                                        progress_callback,
                                        max_connections,
                                        max_retries,
                                        retry_wait,
                                        lease_id,
                                        if_modified_since,
                                        if_unmodified_since,
                                        if_match,
                                        if_none_match,
                                        timeout)
        blob.content = blob.content.decode(encoding)
        return blob

    def get_blob_metadata(
        self, container_name, blob_name, snapshot=None, lease_id=None,
        if_modified_since=None, if_unmodified_since=None, if_match=None,
        if_none_match=None, timeout=None):
        '''
        Returns all user-defined metadata for the specified blob or snapshot.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque value that,
            when present, specifies the blob snapshot to retrieve.
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            A dictionary representing the blob metadata name, value pairs.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('snapshot', _to_str(snapshot)),
            ('comp', 'metadata'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]     

        response = self._perform_request(request)
        return _parse_metadata(response)

    def set_blob_metadata(self, container_name, blob_name,
                          metadata=None, lease_id=None,
                          if_modified_since=None, if_unmodified_since=None,
                          if_match=None, if_none_match=None, timeout=None):
        '''
        Sets user-defined metadata for the specified blob as one or more
        name-value pairs.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param metadata:
            Dict containing name and value pairs. Each call to this operation
            replaces all existing metadata attached to the blob. To remove all
            metadata from the blob, call this operation with no metadata headers.
        :type metadata: a dict mapping str to str
        :param str lease_id:
            Required if the blob has an active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'metadata'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-meta-name-values', metadata),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
            ('x-ms-lease-id', _to_str(lease_id)),
        ]

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def _lease_blob_impl(self, container_name, blob_name,
                         lease_action, lease_id,
                         lease_duration, lease_break_period,
                         proposed_lease_id, if_modified_since,
                         if_unmodified_since, if_match, if_none_match, timeout=None):
        '''
        Establishes and manages a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str lease_action:
            Possible _LeaseActions acquire|renew|release|break|change
        :param str lease_id:
            Required if the blob has an active lease.
        :param int lease_duration:
            Specifies the duration of the lease, in seconds, or negative one
            (-1) for a lease that never expires. A non-infinite lease can be
            between 15 and 60 seconds. A lease duration cannot be changed
            using renew or change.
        :param int lease_break_period:
            For a break operation, this is the proposed duration of
            seconds that the lease should continue before it is broken, between
            0 and 60 seconds. This break period is only used if it is shorter
            than the time remaining on the lease. If longer, the time remaining
            on the lease is used. A new lease will not be available before the
            break period has expired, but the lease may be held for longer than
            the break period. If this header does not appear with a break
            operation, a fixed-duration lease breaks after the remaining lease
            period elapses, and an infinite lease breaks immediately.
        :param str proposed_lease_id:
            Optional for acquire, required for change. Proposed lease ID, in a
            GUID string format. The Blob service returns 400 (Invalid request)
            if the proposed lease ID is not in the correct format. 
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return:
            Response headers returned from the service call.
        :rtype: a dict mapping str to str
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('lease_action', lease_action)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'lease'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-lease-action', _to_str(lease_action)),
            ('x-ms-lease-duration', _to_str(lease_duration)),
            ('x-ms-lease-break-period', _to_str(lease_break_period)),
            ('x-ms-proposed-lease-id', _to_str(proposed_lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]

        return self._perform_request(request)

    def acquire_blob_lease(self, container_name, blob_name,
                           lease_duration=-1,
                           proposed_lease_id=None,
                           if_modified_since=None,
                           if_unmodified_since=None,
                           if_match=None,
                           if_none_match=None, timeout=None):
        '''
        Acquires a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param int lease_duration:
            Specifies the duration of the lease, in seconds, or negative one
            (-1) for a lease that never expires. A non-infinite lease can be
            between 15 and 60 seconds. A lease duration cannot be changed
            using renew or change. Default is -1 (infinite lease).
        :param str proposed_lease_id:
            Proposed lease ID, in a GUID string format. The Blob service
            returns 400 (Invalid request) if the proposed lease ID is not
            in the correct format. 
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: the lease ID of the newly created lease.
        :return: str
        '''
        _validate_not_none('lease_duration', lease_duration)

        if lease_duration is not -1 and\
           (lease_duration < 15 or lease_duration > 60):
            raise ValueError(_ERROR_INVALID_LEASE_DURATION)
        response = self._lease_blob_impl(container_name,
                                     blob_name,
                                     _LeaseActions.Acquire,
                                     None, # lease_id
                                     lease_duration,
                                     None, # lease_break_period
                                     proposed_lease_id,
                                     if_modified_since,
                                     if_unmodified_since,
                                     if_match,
                                     if_none_match,
                                     timeout)
        return _parse_lease_id(response)

    def renew_blob_lease(self, container_name, blob_name,
                         lease_id, if_modified_since=None,
                         if_unmodified_since=None, if_match=None,
                         if_none_match=None, timeout=None):
        '''
        Renews a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str lease_id:
            Lease ID for active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: the lease ID of the renewed lease.
        :return: str
        '''
        _validate_not_none('lease_id', lease_id)

        response = self._lease_blob_impl(container_name,
                                            blob_name,
                                            _LeaseActions.Renew,
                                            lease_id,
                                            None, # lease_duration
                                            None, # lease_break_period
                                            None, # proposed_lease_id
                                            if_modified_since,
                                            if_unmodified_since,
                                            if_match,
                                            if_none_match,
                                            timeout)
        return _parse_lease_id(response)

    def release_blob_lease(self, container_name, blob_name,
                           lease_id, if_modified_since=None,
                           if_unmodified_since=None, if_match=None,
                           if_none_match=None, timeout=None):
        '''
        Releases a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str lease_id:
            Lease ID for active lease.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('lease_id', lease_id)

        self._lease_blob_impl(container_name,
                                blob_name,
                                _LeaseActions.Release,
                                lease_id,
                                None, # lease_duration
                                None, # lease_break_period
                                None, # proposed_lease_id
                                if_modified_since,
                                if_unmodified_since,
                                if_match,
                                if_none_match,
                                timeout)

    def break_blob_lease(self, container_name, blob_name,
                         lease_break_period=None,
                         if_modified_since=None,
                         if_unmodified_since=None,
                         if_match=None,
                         if_none_match=None, timeout=None):
        '''
        Breaks a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param int lease_break_period:
            For a break operation, this is the proposed duration of
            seconds that the lease should continue before it is broken, between
            0 and 60 seconds. This break period is only used if it is shorter
            than the time remaining on the lease. If longer, the time remaining
            on the lease is used. A new lease will not be available before the
            break period has expired, but the lease may be held for longer than
            the break period. If this header does not appear with a break
            operation, a fixed-duration lease breaks after the remaining lease
            period elapses, and an infinite lease breaks immediately.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: Approximate time remaining in the lease period, in seconds.
        :return: int
        '''
        if (lease_break_period is not None) and (lease_break_period < 0 or lease_break_period > 60):
            raise ValueError(_ERROR_INVALID_LEASE_BREAK_PERIOD)

        response = self._lease_blob_impl(container_name,
                                     blob_name,
                                     _LeaseActions.Break,
                                     None, # lease_id
                                     None, # lease_duration
                                     lease_break_period,
                                     None, # proposed_lease_id
                                     if_modified_since,
                                     if_unmodified_since,
                                     if_match,
                                     if_none_match,
                                     timeout)
        return _parse_lease_time(response)

    def change_blob_lease(self, container_name, blob_name,
                         lease_id,
                         proposed_lease_id,
                         if_modified_since=None,
                         if_unmodified_since=None,
                         if_match=None,
                         if_none_match=None, timeout=None):
        '''
        Changes a lock on a blob for write and delete operations.
        The lock duration can be 15 to 60 seconds, or can be infinite.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str lease_id:
            Required if the blob has an active lease.
        :param str proposed_lease_id:
            Proposed lease ID, in a GUID string format. The Blob service returns
            400 (Invalid request) if the proposed lease ID is not in the correct format. 
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        self._lease_blob_impl(container_name,
                                blob_name,
                                _LeaseActions.Change,
                                lease_id,
                                None, # lease_duration
                                None, # lease_break_period
                                proposed_lease_id,
                                if_modified_since,
                                if_unmodified_since,
                                if_match,
                                if_none_match,
                                timeout)

    def snapshot_blob(self, container_name, blob_name,
                      metadata=None, if_modified_since=None,
                      if_unmodified_since=None, if_match=None,
                      if_none_match=None, lease_id=None, timeout=None):
        '''
        Creates a read-only snapshot of a blob.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param metadata:
            Specifies a user-defined name-value pair associated with the blob.
            If no name-value pairs are specified, the operation will copy the
            base blob metadata to the snapshot. If one or more name-value pairs
            are specified, the snapshot is created with the specified metadata,
            and metadata is not copied from the base blob.
        :type metadata: a dict mapping str to str
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: snapshot properties
        :rtype: :class:`~azure.storage.blob.models.Blob`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'snapshot'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-meta-name-values', metadata),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
            ('x-ms-lease-id', _to_str(lease_id))
        ]

        response = self._perform_request(request)
        return _parse_snapshot_blob(blob_name, response)

    def copy_blob(self, container_name, blob_name, copy_source,
                  metadata=None,
                  source_if_modified_since=None,
                  source_if_unmodified_since=None,
                  source_if_match=None, source_if_none_match=None,
                  destination_if_modified_since=None,
                  destination_if_unmodified_since=None,
                  destination_if_match=None,
                  destination_if_none_match=None,
                  destination_lease_id=None,
                  source_lease_id=None, timeout=None):
        '''
        Copies a blob to a destination within the storage account.
        The source for a Copy Blob operation can be a committed blob 
        or an Azure file in any Azure storage account.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str copy_source:
            URL up to 2 KB in length that specifies a blob. A source blob in
            the same account can be private, but a blob in another account
            must be public or accept credentials included in this URL, such as
            a Shared Access Signature. Examples:
            https://myaccount.blob.core.windows.net/mycontainer/myblob
            https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>
        :param metadata:
            Dict containing name and value pairs.
        :type metadata: A dict mapping str to str.
        :param datetime source_if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.  
            Specify this conditional header to copy the blob only if the source
            blob has been modified since the specified date/time.
        :param datetime source_if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this conditional header to copy the blob only if the source blob
            has not been modified since the specified date/time.
        :param ETag source_if_match:
            An ETag value, or the wildcard character (*). Specify this conditional
            header to copy the source blob only if its ETag matches the value
            specified. If the ETag values do not match, the Blob service returns
            status code 412 (Precondition Failed). This header cannot be specified
            if the source is an Azure File.
        :param ETag source_if_none_match:
            An ETag value, or the wildcard character (*). Specify this conditional
            header to copy the blob only if its ETag does not match the value
            specified. If the values are identical, the Blob service returns status
            code 412 (Precondition Failed). This header cannot be specified if the
            source is an Azure File.
        :param datetime destination_if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this conditional header to copy the blob only
            if the destination blob has been modified since the specified date/time.
            If the destination blob has not been modified, the Blob service returns
            status code 412 (Precondition Failed).
        :param datetime destination_if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this conditional header to copy the blob only
            if the destination blob has not been modified since the specified
            date/time. If the destination blob has been modified, the Blob service
            returns status code 412 (Precondition Failed).
        :param ETag destination_if_match:
            An ETag value, or the wildcard character (*). Specify an ETag value for
            this conditional header to copy the blob only if the specified ETag value
            matches the ETag value for an existing destination blob. If the ETag for
            the destination blob does not match the ETag specified for If-Match, the
            Blob service returns status code 412 (Precondition Failed).
        :param ETag destination_if_none_match:
            An ETag value, or the wildcard character (*). Specify an ETag value for
            this conditional header to copy the blob only if the specified ETag value
            does not match the ETag value for the destination blob. Specify the wildcard
            character (*) to perform the operation only if the destination blob does not
            exist. If the specified condition isn't met, the Blob service returns status
            code 412 (Precondition Failed).
        :param str destination_lease_id:
            The lease ID specified for this header must match the lease ID of the
            destination blob. If the request does not include the lease ID or it is not
            valid, the operation fails with status code 412 (Precondition Failed).
        :param str source_lease_id:
            Specify this to perform the Copy Blob operation only if
            the lease ID given matches the active lease ID of the source blob.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: Copy operation properties such as status, source, and ID.
        :rtype: :class:`~azure.storage.blob.models.CopyProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('copy_source', copy_source)

        if copy_source.startswith('/'):
            # Backwards compatibility for earlier versions of the SDK where
            # the copy source can be in the following formats:
            # - Blob in named container:
            #     /accountName/containerName/blobName
            # - Snapshot in named container:
            #     /accountName/containerName/blobName?snapshot=<DateTime>
            # - Blob in root container:
            #     /accountName/blobName
            # - Snapshot in root container:
            #     /accountName/blobName?snapshot=<DateTime>
            account, _, source =\
                copy_source.partition('/')[2].partition('/')
            copy_source = self.protocol + '://' + \
                self.primary_endpoint + '/' + source

        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [('timeout', _int_to_str(timeout))]
        request.headers = [
            ('x-ms-copy-source', _to_str(copy_source)),
            ('x-ms-meta-name-values', metadata),
            ('x-ms-source-if-modified-since',
             _to_str(source_if_modified_since)),
            ('x-ms-source-if-unmodified-since',
             _to_str(source_if_unmodified_since)),
            ('x-ms-source-if-match', _to_str(source_if_match)),
            ('x-ms-source-if-none-match',
             _to_str(source_if_none_match)),
            ('If-Modified-Since', _datetime_to_utc_string(destination_if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(destination_if_unmodified_since)),
            ('If-Match', _to_str(destination_if_match)),
            ('If-None-Match', _to_str(destination_if_none_match)),
            ('x-ms-lease-id', _to_str(destination_lease_id)),
            ('x-ms-source-lease-id', _to_str(source_lease_id))
        ]

        response = self._perform_request(request)
        props = _parse_properties(response, BlobProperties)
        return props.copy

    def abort_copy_blob(self, container_name, blob_name, copy_id,
                        lease_id=None, timeout=None):
        '''
         Aborts a pending copy_blob operation, and leaves a destination blob
         with zero length and full metadata.

         :param str container_name:
             Name of destination container.
         :param str blob_name:
             Name of destination blob.
         :param str copy_id:
             Copy identifier provided in the copy.id of the original
             copy_blob operation.
         :param str lease_id:
             Required if the destination blob has an active infinite lease.
         :param int timeout:
             The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('copy_id', copy_id)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'copy'),
            ('copyid', _to_str(copy_id)),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-copy-action', 'abort'),
        ]

        self._perform_request(request)

    def delete_blob(self, container_name, blob_name, snapshot=None,
                    lease_id=None, delete_snapshots=None,
                    if_modified_since=None, if_unmodified_since=None,
                    if_match=None, if_none_match=None, timeout=None):
        '''
        Marks the specified blob or snapshot for deletion.
        The blob is later deleted during garbage collection.

        Note that in order to delete a blob, you must delete all of its
        snapshots. You can delete both at the same time with the Delete
        Blob operation.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to delete.
        :param str lease_id:
            Required if the blob has an active lease.
        :param delete_snapshots:
            Required if the blob has associated snapshots.
        :type delete_snapshots: 
            One of the values listed in the :class:`~azure.storage.blob.models.DeleteSnapshot` enum.
        :param datetime if_modified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC. 
            Specify this header to perform the operation only
            if the resource has been modified since the specified time.
        :param datetime if_unmodified_since:
            A DateTime value. Azure expects the date value passed in to be UTC.
            If timezone is included, any non-UTC datetimes will be converted to UTC.
            If a date is passed in without timezone info, it is assumed to be UTC.
            Specify this header to perform the operation only if
            the resource has not been modified since the specified date/time.
        :param str if_match:
            An ETag value, or the wildcard character (*). Specify this header to perform
            the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.headers = [
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-delete-snapshots', _to_str(delete_snapshots)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]
        request.query = [
            ('snapshot', _to_str(snapshot)),
            ('timeout', _int_to_str(timeout))
        ]

        self._perform_request(request)
