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
from .._error import (
    _validate_not_none,
    _validate_type_bytes,
    _ERROR_VALUE_NEGATIVE,
)
from .._common_conversion import (
    _int_to_str,
    _to_str,
    _datetime_to_utc_string,
)
from .._serialization import (
    _get_request_body_bytes_only,
)
from .._http import HTTPRequest
from ._error import (
    _ERROR_PAGE_BLOB_SIZE_ALIGNMENT,
)
from ._chunking import (
    _PageBlobChunkUploader,
    _upload_blob_chunks,
)
from .models import (
    _BlobTypes,
    PageBlobProperties,
)
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
)
from ._serialization import (
    _get_path,
    _validate_and_format_range_headers,
)
from ._deserialization import (
    _convert_xml_to_page_ranges,
    _parse_page_properties,
    _parse_base_properties,
)
from .baseblobservice import BaseBlobService
from os import path
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO

# Keep this value sync with _ERROR_PAGE_BLOB_SIZE_ALIGNMENT
_PAGE_ALIGNMENT = 512


class PageBlobService(BaseBlobService):
    '''
    Page blobs are a collection of 512-byte pages optimized for random read and
    write operations. To create a page blob, you initialize the page blob and
    specify the maximum size the page blob will grow. To add or update the
    contents of a page blob, you write a page or pages by specifying an offset
    and a range that align to 512-byte page boundaries. A write to a page blob
    can overwrite just one page, some pages, or up to 4 MB of the page blob.
    Writes to page blobs happen in-place and are immediately committed to the
    blob. The maximum size for a page blob is 1 TB.
    '''

    MAX_PAGE_SIZE = 4 * 1024 * 1024

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
        self.blob_type = _BlobTypes.PageBlob
        super(PageBlobService, self).__init__(
            account_name, account_key, sas_token, is_emulated, protocol, endpoint_suffix, 
            custom_domain, request_session, connection_string)

    def create_blob(
        self, container_name, blob_name, content_length, content_settings=None,
        sequence_number=None, metadata=None, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new Page Blob.

        See create_blob_from_* for high level functions that handle the
        creation and upload of large blobs with automatic chunking and
        progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param int content_length:
            Required. This header specifies the maximum size
            for the page blob, up to 1 TB. The page blob size must be aligned
            to a 512-byte boundary.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set properties on the blob.
        :param int sequence_number:
            The sequence number is a user-controlled value that you can use to
            track requests. The value of the sequence number must be between 0
            and 2^63 - 1.The default value is 0.
        :param metadata:
            Name-value pairs associated with the blob as metadata.
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
        :return: ETag and last modified properties for the new Page Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('content_length', content_length)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [('timeout', _int_to_str(timeout))]
        request.headers = [
            ('x-ms-blob-type', _to_str(self.blob_type)),
            ('x-ms-meta-name-values', metadata),
            ('x-ms-blob-content-length', _to_str(content_length)),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-blob-sequence-number', _to_str(sequence_number)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match))
        ]
        if content_settings is not None:
            request.headers += content_settings._to_headers()

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def update_page(
        self, container_name, blob_name, page, start_range, end_range,
        content_md5=None, lease_id=None, if_sequence_number_lte=None,
        if_sequence_number_lt=None, if_sequence_number_eq=None,
        if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Updates a range of pages.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param bytes page:
            Content of the page.
        :param int start_range:
            Start of byte range to use for writing to a section of the blob.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-1023, etc.
        :param int end_range:
            End of byte range to use for writing to a section of the blob.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-1023, etc.
        :param int content_md5:
            An MD5 hash of the page content. This hash is used to
            verify the integrity of the page during transport. When this header
            is specified, the storage service compares the hash of the content
            that has arrived with the header value that was sent. If the two
            hashes do not match, the operation will fail with error code 400
            (Bad Request).
        :param str lease_id:
            Required if the blob has an active lease.
        :param int if_sequence_number_lte:
            If the blob's sequence number is less than or equal to
            the specified value, the request proceeds; otherwise it fails.
        :param int if_sequence_number_lt:
            If the blob's sequence number is less than the specified
            value, the request proceeds; otherwise it fails.
        :param int if_sequence_number_eq:
            If the blob's sequence number is equal to the specified
            value, the request proceeds; otherwise it fails.
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
            An ETag value, or the wildcard character (*). Specify an ETag value for this conditional
            header to write the page only if the blob's ETag value matches the
            value specified. If the values do not match, the Blob service fails.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify an ETag value for this conditional
            header to write the page only if the blob's ETag value does not
            match the value specified. If the values are identical, the Blob
            service fails.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Page Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('page', page)

        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'page'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('Content-MD5', _to_str(content_md5)),
            ('x-ms-page-write', 'update'),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-if-sequence-number-le',
             _to_str(if_sequence_number_lte)),
            ('x-ms-if-sequence-number-lt',
             _to_str(if_sequence_number_lt)),
            ('x-ms-if-sequence-number-eq',
             _to_str(if_sequence_number_eq)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match))
        ]
        _validate_and_format_range_headers(
            request,
            start_range,
            end_range,
            align_to_page=True)
        request.body = _get_request_body_bytes_only('page', page)

        response = self._perform_request(request)
        return _parse_page_properties(response)

    def clear_page(
        self, container_name, blob_name, start_range, end_range,
        lease_id=None, if_sequence_number_lte=None,
        if_sequence_number_lt=None, if_sequence_number_eq=None,
        if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Clears a range of pages.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param int start_range:
            Start of byte range to use for writing to a section of the blob.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-1023, etc.
        :param int end_range:
            End of byte range to use for writing to a section of the blob.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-1023, etc.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int if_sequence_number_lte:
            If the blob's sequence number is less than or equal to
            the specified value, the request proceeds; otherwise it fails.
        :param int if_sequence_number_lt:
            If the blob's sequence number is less than the specified
            value, the request proceeds; otherwise it fails.
        :param int if_sequence_number_eq:
            If the blob's sequence number is equal to the specified
            value, the request proceeds; otherwise it fails.
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
            An ETag value, or the wildcard character (*). Specify an ETag value for this conditional
            header to write the page only if the blob's ETag value matches the
            value specified. If the values do not match, the Blob service fails.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify an ETag value for this conditional
            header to write the page only if the blob's ETag value does not
            match the value specified. If the values are identical, the Blob
            service fails.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Page Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)

        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'page'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-page-write', 'clear'),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('x-ms-if-sequence-number-le',
             _to_str(if_sequence_number_lte)),
            ('x-ms-if-sequence-number-lt',
             _to_str(if_sequence_number_lt)),
            ('x-ms-if-sequence-number-eq',
             _to_str(if_sequence_number_eq)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match))
        ]
        _validate_and_format_range_headers(
            request,
            start_range,
            end_range,
            align_to_page=True)

        response = self._perform_request(request)
        return _parse_page_properties(response)

    def get_page_ranges(
        self, container_name, blob_name, snapshot=None, start_range=None,
        end_range=None, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
        '''
        Returns the list of valid page ranges for a Page Blob or snapshot
        of a page blob.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            The snapshot parameter is an opaque DateTime value that,
            when present, specifies the blob snapshot to retrieve information
            from.
        :param int start_range:
            Start of byte range to use for getting valid page ranges.
            If no end_range is given, all bytes after the start_range will be searched.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-, etc.
        :param int end_range:
            End of byte range to use for getting valid page ranges.
            If end_range is given, start_range must be provided.
            This range will return valid page ranges for from the offset start up to
            offset end.
            Pages must be aligned with 512-byte boundaries, the start offset
            must be a modulus of 512 and the end offset must be a modulus of
            512-1. Examples of valid byte ranges are 0-511, 512-, etc.
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
        :return: A list of valid Page Ranges for the Page Blob.
        :rtype: list of :class:`~azure.storage.blob.models.PageRange`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'pagelist'),
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
        if start_range is not None:
            _validate_and_format_range_headers(
                request,
                start_range,
                end_range,
                start_range_required=False,
                end_range_required=False,
                align_to_page=True)

        response = self._perform_request(request)
        return _convert_xml_to_page_ranges(response)

    def set_sequence_number(
        self, container_name, blob_name, sequence_number_action, sequence_number=None,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        
        '''
        Sets the blob sequence number.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str sequence_number_action:
            This property indicates how the service should modify the blob's sequence
            number. See :class:`.SequenceNumberAction` for more information.
        :param str sequence_number:
            This property sets the blob's sequence number. The sequence number is a
            user-controlled property that you can use to track requests and manage
            concurrency issues.
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
        :return: ETag and last modified properties for the updated Page Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('sequence_number_action', sequence_number_action)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'properties'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-blob-sequence-number', _to_str(sequence_number)),
            ('x-ms-sequence-number-action', _to_str(sequence_number_action)),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]

        response = self._perform_request(request)
        return _parse_page_properties(response)

    def resize_blob(
        self, container_name, blob_name, content_length,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        
        '''
        Resizes a page blob to the specified size. If the specified value is less
        than the current size of the blob, then all pages above the specified value
        are cleared.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param int content_length:
            Size to resize blob to.
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
        :return: ETag and last modified properties for the updated Page Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('content_length', content_length)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'properties'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('x-ms-blob-content-length', _to_str(content_length)),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]

        response = self._perform_request(request)
        return _parse_page_properties(response)

    #----Convenience APIs-----------------------------------------------------

    def create_blob_from_path(
        self, container_name, blob_name, file_path, content_settings=None,
        metadata=None, progress_callback=None, max_connections=1,
        max_retries=5, retry_wait=1.0, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new blob from a file path, or updates the content of an
        existing blob, with automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param str file_path:
            Path of the file to upload as the blob content.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set blob properties.
        :param metadata:
            Name-value pairs associated with the blob as metadata.
        :type metadata: a dict mapping str to str
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use when the blob size
            exceeds 64MB.
            Set to 1 to upload the blob chunks sequentially.
            Set to 2 or more to upload the blob chunks in parallel. This uses
            more system resources but will upload faster.
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
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
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('file_path', file_path)

        count = path.getsize(file_path)
        with open(file_path, 'rb') as stream:
            self.create_blob_from_stream(
                container_name=container_name,
                blob_name=blob_name,
                stream=stream,
                count=count,
                content_settings=content_settings,
                metadata=metadata,
                progress_callback=progress_callback,
                max_connections=max_connections,
                max_retries=max_retries,
                retry_wait=retry_wait,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_unmodified_since=if_unmodified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)


    def create_blob_from_stream(
        self, container_name, blob_name, stream, count, content_settings=None,
        metadata=None, progress_callback=None, max_connections=1,
        max_retries=5, retry_wait=1.0, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new blob from a file/stream, or updates the content of an
        existing blob, with automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param io.IOBase stream:
            Opened file/stream to upload as the blob content.
        :param int count:
            Number of bytes to read from the stream. This is required, a page
            blob cannot be created if the count is unknown.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set the blob properties.
        :param metadata:
            Name-value pairs associated with the blob as metadata.
        :type metadata: a dict mapping str to str
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use when the blob size
            exceeds 64MB.
            Set to 1 to upload the blob chunks sequentially.
            Set to 2 or more to upload the blob chunks in parallel. This uses
            more system resources but will upload faster.
            Note that parallel upload requires the stream to be seekable.
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
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
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('stream', stream)
        _validate_not_none('count', count)

        if count < 0:
            raise ValueError(_ERROR_VALUE_NEGATIVE.format('count'))

        if count % _PAGE_ALIGNMENT != 0:
            raise ValueError(_ERROR_PAGE_BLOB_SIZE_ALIGNMENT.format(count))

        response = self.create_blob(
            container_name=container_name,
            blob_name=blob_name,
            content_length=count,
            content_settings=content_settings,
            metadata=metadata,
            lease_id=lease_id,
            if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since,
            if_match=if_match,
            if_none_match=if_none_match,
            timeout=timeout
        )

        _upload_blob_chunks(
            blob_service=self,
            container_name=container_name,
            blob_name=blob_name,
            blob_size=count,
            block_size=self.MAX_PAGE_SIZE,
            stream=stream,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_wait=retry_wait,
            progress_callback=progress_callback,
            lease_id=lease_id,
            uploader_class=_PageBlobChunkUploader,
            if_match=response.etag,
            timeout=timeout
        )

    def create_blob_from_bytes(
        self, container_name, blob_name, blob, index=0, count=None,
        content_settings=None, metadata=None, progress_callback=None,
        max_connections=1, max_retries=5, retry_wait=1.0,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new blob from an array of bytes, or updates the content
        of an existing blob, with automatic chunking and progress
        notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param bytes blob:
            Content of blob as an array of bytes.
        :param int index:
            Start index in the byte array.
        :param int count:
            Number of bytes to upload. Set to None or negative value to upload
            all bytes starting from index.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set blob properties.
        :param metadata:
            Name-value pairs associated with the blob as metadata.
        :type metadata: a dict mapping str to str
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_connections:
            Maximum number of parallel connections to use when the blob size
            exceeds 64MB.
            Set to 1 to upload the blob chunks sequentially.
            Set to 2 or more to upload the blob chunks in parallel. This uses
            more system resources but will upload faster.
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
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
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('blob', blob)
        _validate_type_bytes('blob', blob)

        if index < 0:
            raise IndexError(_ERROR_VALUE_NEGATIVE.format('index'))

        if count is None or count < 0:
            count = len(blob) - index

        stream = BytesIO(blob)
        stream.seek(index)

        self.create_blob_from_stream(
            container_name=container_name,
            blob_name=blob_name,
            stream=stream,
            count=count,
            content_settings=content_settings,
            metadata=metadata,
            lease_id=lease_id,
            progress_callback=progress_callback,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_wait=retry_wait,
            if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since,
            if_match=if_match,
            if_none_match=if_none_match,
            timeout=timeout)