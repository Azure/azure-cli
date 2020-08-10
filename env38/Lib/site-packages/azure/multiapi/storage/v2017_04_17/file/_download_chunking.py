# -------------------------------------------------------------------------
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
# --------------------------------------------------------------------------
import threading

from ..common._error import _ERROR_NO_SINGLE_THREAD_CHUNKING


def _download_file_chunks(file_service, share_name, directory_name, file_name,
                          download_size, block_size, progress, start_range, end_range, 
                          stream, max_connections, progress_callback, validate_content, 
                          timeout, operation_context, snapshot):
    if max_connections <= 1:
        raise ValueError(_ERROR_NO_SINGLE_THREAD_CHUNKING.format('file'))

    downloader = _FileChunkDownloader(
        file_service,
        share_name,
        directory_name,
        file_name,
        download_size,
        block_size,
        progress,
        start_range,
        end_range,
        stream,
        progress_callback,
        validate_content,
        timeout,
        operation_context,
        snapshot,
    )

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_connections)
    result = list(executor.map(downloader.process_chunk, downloader.get_chunk_offsets()))


class _FileChunkDownloader(object):
    def __init__(self, file_service, share_name, directory_name, file_name, 
                 download_size, chunk_size, progress, start_range, end_range, 
                 stream, progress_callback, validate_content, timeout, operation_context, snapshot):
        self.file_service = file_service
        self.share_name = share_name
        self.directory_name = directory_name
        self.file_name = file_name
        self.chunk_size = chunk_size

        self.download_size = download_size
        self.start_index = start_range
        self.file_end = end_range

        self.stream = stream
        self.stream_start = stream.tell()
        self.stream_lock = threading.Lock()
        self.progress_callback = progress_callback
        self.progress_total = progress
        self.progress_lock = threading.Lock()
        self.validate_content = validate_content
        self.timeout = timeout
        self.operation_context = operation_context
        self.snapshot = snapshot

    def get_chunk_offsets(self):
        index = self.start_index
        while index < self.file_end:
            yield index
            index += self.chunk_size

    def process_chunk(self, chunk_start):
        if chunk_start + self.chunk_size > self.file_end:
            chunk_end = self.file_end
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
        return self.file_service._get_file(
            self.share_name,
            self.directory_name,
            self.file_name,
            start_range=chunk_start,
            end_range=chunk_end - 1,
            validate_content=self.validate_content,
            timeout=self.timeout,
            _context=self.operation_context,
            snapshot=self.snapshot
        )
