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
    _to_str,
    _int_to_str,
    _datetime_to_utc_string,
)
from .._serialization import (
    _get_request_body_bytes_only,
)
from .._http import HTTPRequest
from ._chunking import (
    _AppendBlobChunkUploader,
    _upload_blob_chunks,
)
from .models import _BlobTypes
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
)
from ._serialization import (
    _get_path,
)
from ._deserialization import (
    _parse_append_block,
    _parse_base_properties,
)
from .baseblobservice import BaseBlobService
from os import path
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO


class AppendBlobService(BaseBlobService):
    '''
    An append blob is comprised of blocks and is optimized for append operations.
    When you modify an append blob, blocks are added to the end of the blob only,
    via the append_block operation. Updating or deleting of existing blocks is not
    supported. Unlike a block blob, an append blob does not expose its block IDs. 

    Each block in an append blob can be a different size, up to a maximum of 4 MB,
    and an append blob can include up to 50,000 blocks. The maximum size of an
    append blob is therefore slightly more than 195 GB (4 MB X 50,000 blocks).
    '''
    MAX_BLOCK_SIZE = 4 * 1024 * 1024

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
        self.blob_type = _BlobTypes.AppendBlob
        super(AppendBlobService, self).__init__(
            account_name, account_key, sas_token, is_emulated, protocol, endpoint_suffix, 
            custom_domain, request_session, connection_string)

    def create_blob(self, container_name, blob_name, content_settings=None,
                    metadata=None, lease_id=None,
                    if_modified_since=None, if_unmodified_since=None,
                    if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a blob or overrides an existing blob. Use if_match=* to
        prevent overriding an existing blob. 

        See create_blob_from_* for high level
        functions that handle the creation and upload of large blobs with
        automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set blob properties.
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
            An ETag value, or the wildcard character (*). Specify this header to
            perform the operation only if the resource's ETag matches the value specified.
        :param str if_none_match:
            An ETag value, or the wildcard character (*). Specify this header
            to perform the operation only if the resource's ETag does not match
            the value specified. Specify the wildcard character (*) to perform
            the operation only if the resource does not exist, and fail the
            operation if it does exist.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: ETag and last modified properties for the updated Append Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [('timeout', _int_to_str(timeout))]
        request.headers = [
            ('x-ms-blob-type', _to_str(self.blob_type)),
            ('x-ms-meta-name-values', metadata),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match))
        ]
        if content_settings is not None:
            request.headers += content_settings._to_headers()

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def append_block(self, container_name, blob_name, block,
                     content_md5=None, maxsize_condition=None,
                     appendpos_condition=None,
                     lease_id=None, if_modified_since=None,
                     if_unmodified_since=None, if_match=None,
                     if_none_match=None, timeout=None):
        '''
        Commits a new block of data to the end of an existing append blob.
        
        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param bytes block:
            Content of the block in bytes.
        :param int content_md5:
            An MD5 hash of the block content. This hash is used to
            verify the integrity of the blob during transport. When this
            header is specified, the storage service checks the hash that has
            arrived with the one that was sent.
        :param int maxsize_condition:
            Optional conditional header. The max length in bytes permitted for
            the append blob. If the Append Block operation would cause the blob
            to exceed that limit or if the blob size is already greater than the
            value specified in this header, the request will fail with
            MaxBlobSizeConditionNotMet error (HTTP status code 412 – Precondition Failed).
        :param int appendpos_condition:
            Optional conditional header, used only for the Append Block operation.
            A number indicating the byte offset to compare. Append Block will
            succeed only if the append position is equal to this number. If it
            is not, the request will fail with the
            AppendPositionConditionNotMet error
            (HTTP status code 412 – Precondition Failed).
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
            ETag, last modified, append offset, and committed block count 
            properties for the updated Append Blob
        :rtype: :class:`~azure.storage.blob.models.AppendBlockProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('block', block)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'appendblock'),
            ('timeout', _int_to_str(timeout)),
         ]
        request.headers = [
            ('Content-MD5', _to_str(content_md5)),
            ('x-ms-blob-condition-maxsize', _to_str(maxsize_condition)),
            ('x-ms-blob-condition-appendpos', _to_str(appendpos_condition)),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match))
        ]
        request.body = _get_request_body_bytes_only('block', block)

        response = self._perform_request(request)
        return _parse_append_block(response)

    #----Convenience APIs----------------------------------------------

    def append_blob_from_path(
        self, container_name, blob_name, file_path,
        maxsize_condition=None, progress_callback=None,
        max_retries=5, retry_wait=1.0, lease_id=None, timeout=None):
        '''
        Appends to the content of an existing blob from a file path, with automatic
        chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param str file_path:
            Path of the file to upload as the blob content.
        :param int maxsize_condition:
            Optional conditional header. The max length in bytes permitted for
            the append blob. If the Append Block operation would cause the blob
            to exceed that limit or if the blob size is already greater than the
            value specified in this header, the request will fail with
            MaxBlobSizeConditionNotMet error (HTTP status code 412 – Precondition Failed).
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
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
            self.append_blob_from_stream(
                container_name,
                blob_name,
                stream,
                count=count,
                maxsize_condition=maxsize_condition,
                progress_callback=progress_callback,
                max_retries=max_retries,
                retry_wait=retry_wait,
                lease_id=lease_id,
                timeout=timeout)

    def append_blob_from_bytes(
        self, container_name, blob_name, blob, index=0, count=None,
        maxsize_condition=None, progress_callback=None,
        max_retries=5, retry_wait=1.0, lease_id=None, timeout=None):
        '''
        Appends to the content of an existing blob from an array of bytes, with
        automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param bytes blob:
            Content of blob as an array of bytes.
        :param int index:
            Start index in the array of bytes.
        :param int count:
            Number of bytes to upload. Set to None or negative value to upload
            all bytes starting from index.
        :param int maxsize_condition:
            Optional conditional header. The max length in bytes permitted for
            the append blob. If the Append Block operation would cause the blob
            to exceed that limit or if the blob size is already greater than the
            value specified in this header, the request will fail with
            MaxBlobSizeConditionNotMet error (HTTP status code 412 – Precondition Failed).
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('blob', blob)
        _validate_not_none('index', index)
        _validate_type_bytes('blob', blob)

        if index < 0:
            raise IndexError(_ERROR_VALUE_NEGATIVE.format('index'))

        if count is None or count < 0:
            count = len(blob) - index

        stream = BytesIO(blob)
        stream.seek(index)

        self.append_blob_from_stream(
            container_name,
            blob_name,
            stream,
            count=count,
            maxsize_condition=maxsize_condition,
            lease_id=lease_id,
            progress_callback=progress_callback,
            max_retries=max_retries,
            retry_wait=retry_wait,
            timeout=timeout)

    def append_blob_from_text(
        self, container_name, blob_name, text, encoding='utf-8',
        maxsize_condition=None, progress_callback=None,
        max_retries=5, retry_wait=1.0, lease_id=None, timeout=None):
        '''
        Appends to the content of an existing blob from str/unicode, with
        automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param str text:
            Text to upload to the blob.
        :param str encoding:
            Python encoding to use to convert the text to bytes.
        :param int maxsize_condition:
            Optional conditional header. The max length in bytes permitted for
            the append blob. If the Append Block operation would cause the blob
            to exceed that limit or if the blob size is already greater than the
            value specified in this header, the request will fail with
            MaxBlobSizeConditionNotMet error (HTTP status code 412 – Precondition Failed).
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('text', text)

        if not isinstance(text, bytes):
            _validate_not_none('encoding', encoding)
            text = text.encode(encoding)

        self.append_blob_from_bytes(
            container_name,
            blob_name,
            text,
            index=0,
            count=len(text),
            maxsize_condition=maxsize_condition,
            lease_id=lease_id,
            progress_callback=progress_callback,
            max_retries=max_retries,
            retry_wait=retry_wait,
            timeout=timeout)

    def append_blob_from_stream(
        self, container_name, blob_name, stream, count=None,
        maxsize_condition=None, progress_callback=None, 
        max_retries=5, retry_wait=1.0, lease_id=None, timeout=None):
        '''
        Appends to the content of an existing blob from a file/stream, with
        automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param io.IOBase stream:
            Opened stream to upload as the blob content.
        :param int count:
            Number of bytes to read from the stream. This is optional, but
            should be supplied for optimal performance.
        :param int maxsize_condition:
            Conditional header. The max length in bytes permitted for
            the append blob. If the Append Block operation would cause the blob
            to exceed that limit or if the blob size is already greater than the
            value specified in this header, the request will fail with
            MaxBlobSizeConditionNotMet error (HTTP status code 412 – Precondition Failed).
        :param progress_callback:
            Callback for progress with signature function(current, total) where
            current is the number of bytes transfered so far, and total is the
            size of the blob, or None if the total size is unknown.
        :type progress_callback: callback function in format of func(current, total)
        :param int max_retries:
            Number of times to retry upload of blob chunk if an error occurs.
        :param int retry_wait:
            Sleep time in secs between retries.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds. This method may make 
            multiple calls to the Azure service and the timeout will apply to 
            each call individually.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('stream', stream)

        _upload_blob_chunks(
            blob_service=self,
            container_name=container_name,
            blob_name=blob_name,
            blob_size=count,
            block_size=self.MAX_BLOCK_SIZE,
            stream=stream,
            max_connections=1, # upload not easily parallelizable
            max_retries=max_retries,
            retry_wait=retry_wait,
            progress_callback=progress_callback,
            lease_id=lease_id,
            uploader_class=_AppendBlobChunkUploader,
            maxsize_condition=maxsize_condition,
            timeout=timeout
        )