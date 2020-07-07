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

_ERROR_PAGE_BLOB_SIZE_ALIGNMENT = \
    'Invalid page blob size: {0}. ' + \
    'The size must be aligned to a 512-byte boundary.'

_ERROR_PAGE_BLOB_START_ALIGNMENT = \
    'start_range must align with 512 page size'

_ERROR_PAGE_BLOB_END_ALIGNMENT = \
    'end_range must align with 512 page size'

_ERROR_INVALID_BLOCK_ID = \
    'All blocks in block list need to have valid block ids.'

_ERROR_INVALID_LEASE_DURATION = \
    "lease_duration param needs to be between 15 and 60 or -1."

_ERROR_INVALID_LEASE_BREAK_PERIOD = \
    "lease_break_period param needs to be between 0 and 60."

_ERROR_NO_SINGLE_THREAD_CHUNKING = \
    'To use blob chunk downloader more than 1 thread must be ' + \
    'used since get_blob_to_bytes should be called for single threaded ' + \
    'blob downloads.'