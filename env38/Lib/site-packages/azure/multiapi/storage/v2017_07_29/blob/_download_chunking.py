# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import threading

from ..common._error import _ERROR_NO_SINGLE_THREAD_CHUNKING


def _download_blob_chunks(blob_service, container_name, blob_name, snapshot,
                          download_size, block_size, progress, start_range, end_range,
                          stream, max_connections, progress_callback, validate_content,
                          lease_id, if_modified_since, if_unmodified_since, if_match,
                          if_none_match, timeout, operation_context):
    if max_connections <= 1:
        raise ValueError(_ERROR_NO_SINGLE_THREAD_CHUNKING.format('blob'))

    downloader = _BlobChunkDownloader(
        blob_service,
        container_name,
        blob_name,
        snapshot,
        download_size,
        block_size,
        progress,
        start_range,
        end_range,
        stream,
        progress_callback,
        validate_content,
        lease_id,
        if_modified_since,
        if_unmodified_since,
        if_match,
        if_none_match,
        timeout,
        operation_context,
    )

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_connections)
    result = list(executor.map(downloader.process_chunk, downloader.get_chunk_offsets()))


class _BlobChunkDownloader(object):
    def __init__(self, blob_service, container_name, blob_name, snapshot, download_size,
                 chunk_size, progress, start_range, end_range, stream,
                 progress_callback, validate_content, lease_id, if_modified_since,
                 if_unmodified_since, if_match, if_none_match, timeout, operation_context):
        self.blob_service = blob_service
        self.container_name = container_name
        self.blob_name = blob_name
        self.snapshot = snapshot
        self.chunk_size = chunk_size

        self.download_size = download_size
        self.start_index = start_range
        self.blob_end = end_range

        self.stream = stream
        self.stream_start = stream.tell()
        self.stream_lock = threading.Lock()
        self.progress_callback = progress_callback
        self.progress_total = progress
        self.progress_lock = threading.Lock()
        self.timeout = timeout
        self.operation_context = operation_context

        self.validate_content = validate_content
        self.lease_id = lease_id
        self.if_modified_since = if_modified_since
        self.if_unmodified_since = if_unmodified_since
        self.if_match = if_match
        self.if_none_match = if_none_match

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

        chunk_data = self._download_chunk(chunk_start, chunk_end).content
        length = chunk_end - chunk_start
        if length > 0:
            self._write_to_stream(chunk_data, chunk_start)
            self._update_progress(length)

    def _update_progress(self, length):
        if self.progress_callback is not None:
            with self.progress_lock:
                self.progress_total += length
                total = self.progress_total
                self.progress_callback(total, self.download_size)

    def _write_to_stream(self, chunk_data, chunk_start):
        with self.stream_lock:
            self.stream.seek(self.stream_start + (chunk_start - self.start_index))
            self.stream.write(chunk_data)

    def _download_chunk(self, chunk_start, chunk_end):
        response = self.blob_service._get_blob(
            self.container_name,
            self.blob_name,
            snapshot=self.snapshot,
            start_range=chunk_start,
            end_range=chunk_end - 1,
            validate_content=self.validate_content,
            lease_id=self.lease_id,
            if_modified_since=self.if_modified_since,
            if_unmodified_since=self.if_unmodified_since,
            if_match=self.if_match,
            if_none_match=self.if_none_match,
            timeout=self.timeout,
            _context=self.operation_context
        )

        # This makes sure that if_match is set so that we can validate 
        # that subsequent downloads are to an unmodified blob
        self.if_match = response.properties.etag
        return response
