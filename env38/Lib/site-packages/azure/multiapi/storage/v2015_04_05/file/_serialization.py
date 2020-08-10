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
from time import time
from wsgiref.handlers import format_date_time
from .._error import (
    _validate_not_none,
    _ERROR_START_END_NEEDED_FOR_MD5,
    _ERROR_RANGE_TOO_LARGE_FOR_MD5,
)
from .._common_conversion import _str

def _get_path(share_name=None, directory_name=None, file_name=None):
    '''
    Creates the path to access a file resource.

    share_name:
        Name of share.
    directory_name:
        The path to the directory.
    file_name:
        Name of file.
    '''
    if share_name and directory_name and file_name:
        return '/{0}/{1}/{2}'.format(
            _str(share_name),
            _str(directory_name),
            _str(file_name))
    elif share_name and directory_name:
        return '/{0}/{1}'.format(
            _str(share_name),
            _str(directory_name))
    elif share_name and file_name:
        return '/{0}/{1}'.format(
            _str(share_name),
            _str(file_name))
    elif share_name:
        return '/{0}'.format(_str(share_name))
    else:
        return '/'

def _validate_and_format_range_headers(request, start_range, end_range, start_range_required=True, end_range_required=True, check_content_md5=False):
    request.headers = request.headers or []
    if start_range_required == True:
        _validate_not_none('start_range', start_range)
    if end_range_required == True:
        _validate_not_none('end_range', end_range)
    if end_range_required == True or end_range is not None:
        _validate_not_none('end_range', end_range)        
        request.headers.append(('x-ms-range', "bytes={0}-{1}".format(start_range, end_range)))
    else:
        request.headers.append(('x-ms-range', "bytes={0}-".format(start_range)))

    if check_content_md5 == True:
        if start_range is None or end_range is None:
            raise ValueError(_ERROR_START_END_NEEDED_FOR_MD5)
        if end_range - start_range > 4 * 1024 * 1024:
            raise ValueError(_ERROR_RANGE_TOO_LARGE_FOR_MD5)

        request.headers.append(('x-ms-range-get-content-md5', 'true'))