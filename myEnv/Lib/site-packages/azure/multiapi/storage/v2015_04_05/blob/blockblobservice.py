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
    _encode_base64,
    _to_str,
    _int_to_str,
    _datetime_to_utc_string,
)
from .._serialization import (
    _get_request_body,
    _get_request_body_bytes_only,
)
from .._http import HTTPRequest
from ._chunking import (
    _BlockBlobChunkUploader,
    _upload_blob_chunks,
)
from .models import (
    _BlobTypes,
)
from .._constants import (
    SERVICE_HOST_BASE,
    DEFAULT_PROTOCOL,
)
from ._serialization import (
    _convert_block_list_to_xml,
    _get_path,
)
from ._deserialization import (
    _convert_xml_to_block_list,
    _parse_base_properties,
)
from .baseblobservice import BaseBlobService
from os import path
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO


class BlockBlobService(BaseBlobService):
    '''
    Block blobs let you upload large blobs efficiently. Block blobs are comprised
    of blocks, each of which is identified by a block ID. You create or modify a
    block blob by writing a set of blocks and committing them by their block IDs.
    Each block can be a different size, up to a maximum of 4 MB, and a block blob
    can include up to 50,000 blocks. The maximum size of a block blob is therefore
    slightly more than 195 GB (4 MB X 50,000 blocks). If you are writing a block
    blob that is no more than 64 MB in size, you can upload it in its entirety with
    a single write operation; see create_blob_from_bytes. 
    '''

    MAX_SINGLE_PUT_SIZE = 64 * 1024 * 1024
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
        self.blob_type = _BlobTypes.BlockBlob
        super(BlockBlobService, self).__init__(
            account_name, account_key, sas_token, is_emulated, protocol, endpoint_suffix, 
            custom_domain, request_session, connection_string)

    def _put_blob(self, container_name, blob_name, blob, content_settings=None,
                  metadata=None, lease_id=None, if_modified_since=None,
                  if_unmodified_since=None, if_match=None,
                  if_none_match=None, timeout=None):
        '''
        Creates a blob or updates an existing blob.

        See create_blob_from_* for high level
        functions that handle the creation and upload of large blobs with
        automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param bytes blob:
            Content of blob as bytes (size < 64MB). For larger size, you
            must call put_block and put_block_list to set content of blob.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set properties on the blob.
        :param metadata:
            Name-value pairs associated with the blob as metadata.
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
        :return: ETag and last modified properties for the new Block Blob
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
        request.body = _get_request_body_bytes_only('blob', blob)

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def put_block(self, container_name, blob_name, block, block_id,
                  content_md5=None, lease_id=None, timeout=None):
        '''
        Creates a new block to be committed as part of a blob.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param bytes block:
            Content of the block.
        :param str block_id:
            A valid Base64 string value that identifies the block. Prior to
            encoding, the string must be less than or equal to 64 bytes in size.
            For a given blob, the length of the value specified for the blockid
            parameter must be the same size for each block. Note that the Base64
            string must be URL-encoded.
        :param int content_md5:
            An MD5 hash of the block content. This hash is used to
            verify the integrity of the blob during transport. When this
            header is specified, the storage service checks the hash that has
            arrived with the one that was sent.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('block', block)
        _validate_not_none('block_id', block_id)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'block'),
            ('blockid', _encode_base64(_to_str(block_id))),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('Content-MD5', _to_str(content_md5)),
            ('x-ms-lease-id', _to_str(lease_id))
        ]
        request.body = _get_request_body_bytes_only('block', block)

        self._perform_request(request)

    def put_block_list(
        self, container_name, blob_name, block_list,
        transactional_content_md5=None, content_settings=None,
        metadata=None, lease_id=None, if_modified_since=None,
        if_unmodified_since=None, if_match=None, if_none_match=None, 
        timeout=None):
        '''
        Writes a blob by specifying the list of block IDs that make up the blob.
        In order to be written as part of a blob, a block must have been
        successfully written to the server in a prior Put Block operation.

        You can call Put Block List to update a blob by uploading only those
        blocks that have changed, then committing the new and existing blocks
        together. You can do this by specifying whether to commit a block from
        the committed block list or from the uncommitted block list, or to commit
        the most recently uploaded version of the block, whichever list it may
        belong to.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param block_list:
            A list of :class:`~azure.storeage.blob.models.BlobBlock` containing the block ids and block state.
        :type block_list: list of :class:`~azure.storage.blob.models.BlobBlock`
        :param str transactional_content_md5:
            An MD5 hash of the block content. This hash is used to
            verify the integrity of the blob during transport. When this header
            is specified, the storage service checks the hash that has arrived
            with the one that was sent.
        :param ~azure.storage.blob.models.ContentSettings content_settings:
            ContentSettings object used to set properties on the blob.
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
        :return: ETag and last modified properties for the updated Block Blob
        :rtype: :class:`~azure.storage.blob.models.ResourceProperties`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        _validate_not_none('block_list', block_list)
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'blocklist'),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [
            ('Content-MD5', _to_str(transactional_content_md5)),
            ('x-ms-meta-name-values', metadata),
            ('x-ms-lease-id', _to_str(lease_id)),
            ('If-Modified-Since', _datetime_to_utc_string(if_modified_since)),
            ('If-Unmodified-Since', _datetime_to_utc_string(if_unmodified_since)),
            ('If-Match', _to_str(if_match)),
            ('If-None-Match', _to_str(if_none_match)),
        ]
        if content_settings is not None:
            request.headers += content_settings._to_headers()
        request.body = _get_request_body(
            _convert_block_list_to_xml(block_list))

        response = self._perform_request(request)
        return _parse_base_properties(response)

    def get_block_list(self, container_name, blob_name, snapshot=None,
                       block_list_type=None, lease_id=None, timeout=None):
        '''
        Retrieves the list of blocks that have been uploaded as part of a
        block blob. There are two block lists maintained for a blob:
            Committed Block List:
                The list of blocks that have been successfully committed to a
                given blob with Put Block List.
            Uncommitted Block List:
                The list of blocks that have been uploaded for a blob using
                Put Block, but that have not yet been committed. These blocks
                are stored in Azure in association with a blob, but do not yet
                form part of the blob.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of existing blob.
        :param str snapshot:
            Datetime to determine the time to retrieve the blocks.
        :param str block_list_type:
            Specifies whether to return the list of committed blocks, the list
            of uncommitted blocks, or both lists together. Valid values are:
            committed, uncommitted, or all.
        :param str lease_id:
            Required if the blob has an active lease.
        :param int timeout:
            The timeout parameter is expressed in seconds.
        :return: list committed and/or uncommitted blocks for Block Blob
        :rtype: :class:`~azure.storage.blob.models.BlobBlockList`
        '''
        _validate_not_none('container_name', container_name)
        _validate_not_none('blob_name', blob_name)
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self._get_host()
        request.path = _get_path(container_name, blob_name)
        request.query = [
            ('comp', 'blocklist'),
            ('snapshot', _to_str(snapshot)),
            ('blocklisttype', _to_str(block_list_type)),
            ('timeout', _int_to_str(timeout)),
        ]
        request.headers = [('x-ms-lease-id', _to_str(lease_id))]

        response = self._perform_request(request)
        return _convert_xml_to_block_list(response)

    #----Convenience APIs-----------------------------------------------------

    def create_blob_from_path(
        self, container_name, blob_name, file_path, content_settings=None,
        metadata=None, progress_callback=None,
        max_connections=1, max_retries=5, retry_wait=1.0,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
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

    def create_blob_from_stream(
        self, container_name, blob_name, stream, count=None,
        content_settings=None, metadata=None, progress_callback=None,
        max_connections=1, max_retries=5, retry_wait=1.0,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new blob from a file/stream, or updates the content of
        an existing blob, with automatic chunking and progress
        notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param io.IOBase stream:
            Opened file/stream to upload as the blob content.
        :param int count:
            Number of bytes to read from the stream. This is optional, but
            should be supplied for optimal performance.
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

        if count and count < self.MAX_SINGLE_PUT_SIZE:
            if progress_callback:
                progress_callback(0, count)

            data = stream.read(count)
            self._put_blob(
                container_name=container_name,
                blob_name=blob_name,
                blob=data,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_unmodified_since=if_unmodified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)

            if progress_callback:
                progress_callback(count, count)
        else:
            block_ids = _upload_blob_chunks(
                blob_service=self,
                container_name=container_name,
                blob_name=blob_name,
                blob_size=count,
                block_size=self.MAX_BLOCK_SIZE,
                stream=stream,
                max_connections=max_connections,
                max_retries=max_retries,
                retry_wait=retry_wait,
                progress_callback=progress_callback,
                lease_id=lease_id,
                uploader_class=_BlockBlobChunkUploader,
                timeout=timeout
            )

            self.put_block_list(
                container_name=container_name,
                blob_name=blob_name,
                block_list=block_ids,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_unmodified_since=if_unmodified_since,
                if_match=if_match,
                if_none_match=if_none_match,
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
            Start index in the array of bytes.
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
        _validate_not_none('index', index)
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

    def create_blob_from_text(
        self, container_name, blob_name, text, encoding='utf-8',
        content_settings=None, metadata=None, progress_callback=None,
        max_connections=1, max_retries=5, retry_wait=1.0,
        lease_id=None, if_modified_since=None, if_unmodified_since=None,
        if_match=None, if_none_match=None, timeout=None):
        '''
        Creates a new blob from str/unicode, or updates the content of an
        existing blob, with automatic chunking and progress notifications.

        :param str container_name:
            Name of existing container.
        :param str blob_name:
            Name of blob to create or update.
        :param str text:
            Text to upload to the blob.
        :param str encoding:
            Python encoding to use to convert the text to bytes.
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
        _validate_not_none('text', text)

        if not isinstance(text, bytes):
            _validate_not_none('encoding', encoding)
            text = text.encode(encoding)

        self.create_blob_from_bytes(
            container_name=container_name,
            blob_name=blob_name,
            blob=text,
            index=0,
            count=len(text),
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