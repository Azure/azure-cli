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
import threading

from time import sleep
from .._common_conversion import _encode_base64
from .._serialization import url_quote
from azure.common import (
    AzureHttpError,
)
from .._error import _ERROR_NO_SINGLE_THREAD_CHUNKING
from .models import BlobBlock


class _BlobChunkDownloader(object):
    def __init__(self, blob_service, container_name, blob_name, blob_size,
                 chunk_size, start_range, end_range, stream, max_retries,
                 retry_wait, progress_callback, if_modified_since, 
                 if_unmodified_since, if_match, if_none_match, timeout):
        self.blob_service = blob_service
        self.container_name = container_name
        self.blob_name = blob_name
        self.chunk_size = chunk_size
        if start_range is not None:
            end_range = end_range or blob_size
            self.blob_size = end_range - start_range
            self.blob_end = end_range
            self.start_index = start_range
        else:
            self.blob_size = blob_size
            self.blob_end = blob_size
            self.start_index = 0

        self.stream = stream
        self.stream_start = stream.tell()
        self.stream_lock = threading.Lock()
        self.progress_callback = progress_callback
        self.progress_total = 0
        self.progress_lock = threading.Lock()
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.timeout = timeout

        self.if_modified_since=if_modified_since
        self.if_unmodified_since=if_unmodified_since
        self.if_match=if_match
        self.if_none_match=if_none_match

    def get_chunk_offsets(self):
        index = self.start_index
        while index < self.blob_end:
            yield index
            index += self.chunk_size

    def process_chunk(self, chunk_start):
        if chunk_start + self.chunk_size > self.blob_end:
            chunk_end = self.blob_end
        else:
            chunk_end = chunk_start + self.chunk_size

        chunk_data = self._download_chunk_with_retries(chunk_start, chunk_end).content
        length = chunk_end - chunk_start
        if length > 0:
            self._write_to_stream(chunk_data, chunk_start)
            self._update_progress(length)

    def _update_progress(self, length):
        if self.progress_callback is not None:
            with self.progress_lock:
                self.progress_total += length
                total = self.progress_total
                self.progress_callback(total, self.blob_size)

    def _write_to_stream(self, chunk_data, chunk_start):
        with self.stream_lock:
            self.stream.seek(self.stream_start + chunk_start)
            self.stream.write(chunk_data)

    def _download_chunk_with_retries(self, chunk_start, chunk_end):
        retries = self.max_retries
        while True:
            try:
                response = self.blob_service._get_blob(
                    self.container_name,
                    self.blob_name,
                    start_range=chunk_start,
                    end_range=chunk_end - 1,
                    if_modified_since=self.if_modified_since,
                    if_unmodified_since=self.if_unmodified_since,
                    if_match=self.if_match,
                    if_none_match=self.if_none_match,
                    timeout=self.timeout
                )

                # This makes sure that if_match is set so that we can validate 
                # that subsequent downloads are to an unmodified blob
                self.if_match = response.properties.etag
                return response
            except AzureHttpError:
                if retries > 0:
                    retries -= 1
                    sleep(self.retry_wait)
                else:
                    raise


class _BlobChunkUploader(object):
    def __init__(self, blob_service, container_name, blob_name, blob_size,
                 chunk_size, stream, parallel, max_retries, retry_wait,
                 progress_callback, lease_id, timeout):
        self.blob_service = blob_service
        self.container_name = container_name
        self.blob_name = blob_name
        self.blob_size = blob_size
        self.chunk_size = chunk_size
        self.stream = stream
        self.parallel = parallel
        self.stream_start = stream.tell() if parallel else None
        self.stream_lock = threading.Lock() if parallel else None
        self.progress_callback = progress_callback
        self.progress_total = 0
        self.progress_lock = threading.Lock() if parallel else None
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.lease_id = lease_id
        self.timeout = timeout

    def get_chunk_offsets(self):
        index = 0
        if self.blob_size is None:
            # we don't know the size of the stream, so we have no
            # choice but to seek
            while True:
                data = self._read_from_stream(index, 1)
                if not data:
                    break
                yield index
                index += self.chunk_size
        else:
            while index < self.blob_size:
                yield index
                index += self.chunk_size

    def process_chunk(self, chunk_offset):
        size = self.chunk_size
        if self.blob_size is not None:
            size = min(size, self.blob_size - chunk_offset)
        chunk_data = self._read_from_stream(chunk_offset, size)
        return self._upload_chunk_with_retries(chunk_offset, chunk_data)

    def process_all_unknown_size(self):
        assert self.stream_lock is None
        range_ids = []
        index = 0
        while True:
            data = self._read_from_stream(None, self.chunk_size)
            if data:
                range_id = self._upload_chunk_with_retries(index, data)
                index += len(data)
                range_ids.append(range_id)
            else:
                break

        return range_ids

    def _read_from_stream(self, offset, count):
        if self.stream_lock is not None:
            with self.stream_lock:
                self.stream.seek(self.stream_start + offset)
                data = self.stream.read(count)
        else:
            data = self.stream.read(count)
        return data

    def _update_progress(self, length):
        if self.progress_callback is not None:
            if self.progress_lock is not None:
                with self.progress_lock:
                    self.progress_total += length
                    total = self.progress_total
            else:
                self.progress_total += length
                total = self.progress_total
            self.progress_callback(total, self.blob_size)

    def _upload_chunk_with_retries(self, chunk_offset, chunk_data):
        retries = self.max_retries
        while True:
            try:
                range_id = self._upload_chunk(chunk_offset, chunk_data) 
                self._update_progress(len(chunk_data))
                return range_id
            except AzureHttpError:
                if retries > 0:
                    retries -= 1
                    sleep(self.retry_wait)
                else:
                    raise


class _BlockBlobChunkUploader(_BlobChunkUploader):
    def _upload_chunk(self, chunk_offset, chunk_data):
        block_id=url_quote(_encode_base64('{0:032d}'.format(chunk_offset)))
        self.blob_service.put_block(
            self.container_name,
            self.blob_name,
            chunk_data,
            block_id,
            lease_id=self.lease_id,
            timeout=self.timeout,
        )
        return BlobBlock(block_id)


class _PageBlobChunkUploader(_BlobChunkUploader):
    def _upload_chunk(self, chunk_start, chunk_data):
        chunk_end = chunk_start + len(chunk_data) - 1
        resp = self.blob_service.update_page(
            self.container_name,
            self.blob_name,
            chunk_data,
            chunk_start,
            chunk_end,
            lease_id=self.lease_id,
            if_match=self.if_match,
            timeout=self.timeout,
        )

        if not self.parallel:
            self.if_match = resp.etag

class _AppendBlobChunkUploader(_BlobChunkUploader):
    def _upload_chunk(self, chunk_offset, chunk_data):
        if not hasattr(self, 'current_length'):
            resp = self.blob_service.append_block(
                self.container_name,
                self.blob_name,
                chunk_data,
                lease_id=self.lease_id,
                maxsize_condition=self.maxsize_condition,
                timeout=self.timeout,
            )

            self.current_length = resp.append_offset
        else:
            resp = self.blob_service.append_block(
                self.container_name,
                self.blob_name,
                chunk_data,
                lease_id=self.lease_id,
                maxsize_condition=self.maxsize_condition,
                appendpos_condition=self.current_length + chunk_offset,
                timeout=self.timeout,
            )


def _download_blob_chunks(blob_service, container_name, blob_name,
                          blob_size, block_size, start_range, end_range, stream,
                          max_connections, max_retries, retry_wait, progress_callback,
                          if_modified_since, if_unmodified_since, if_match, if_none_match, 
                          timeout):
    if max_connections <= 1:
        raise ValueError(_ERROR_NO_SINGLE_THREAD_CHUNKING.format('blob'))

    downloader = _BlobChunkDownloader(
        blob_service,
        container_name,
        blob_name,
        blob_size,
        block_size,
        start_range,
        end_range,
        stream,
        max_retries,
        retry_wait,
        progress_callback,
        if_modified_since,
        if_unmodified_since,
        if_match,
        if_none_match,
        timeout
    )

    if progress_callback is not None:
        progress_callback(0, blob_size)

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_connections)
    result = list(executor.map(downloader.process_chunk, downloader.get_chunk_offsets()))


def _upload_blob_chunks(blob_service, container_name, blob_name,
                        blob_size, block_size, stream, max_connections,
                        max_retries, retry_wait, progress_callback,
                        lease_id, uploader_class, maxsize_condition=None, 
                        if_match=None, timeout=None):
    uploader = uploader_class(
        blob_service,
        container_name,
        blob_name,
        blob_size,
        block_size,
        stream,
        max_connections > 1,
        max_retries,
        retry_wait,
        progress_callback,
        lease_id,
        timeout
    )

    uploader.maxsize_condition = maxsize_condition

    # ETag matching does not work with parallelism as a ranged upload may start 
    # before the previous finishes and provides an etag
    uploader.if_match = if_match if not max_connections > 1 else None

    if progress_callback is not None:
        progress_callback(0, blob_size)

    if max_connections > 1:
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_connections)
        range_ids = list(executor.map(uploader.process_chunk, uploader.get_chunk_offsets()))
    else:
        if blob_size is not None:
            range_ids = [uploader.process_chunk(start) for start in uploader.get_chunk_offsets()]
        else:
            range_ids = uploader.process_all_unknown_size()

    return range_ids
