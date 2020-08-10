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

from azure.common import (
    AzureHttpError,
    AzureConflictHttpError,
    AzureMissingResourceHttpError,
)

_ERROR_CONFLICT = 'Conflict ({0})'
_ERROR_NOT_FOUND = 'Not found ({0})'
_ERROR_UNKNOWN = 'Unknown error ({0})'
_ERROR_STORAGE_MISSING_INFO = \
    'You need to provide an account name and either an account_key or sas_token when creating a storage service.'
_ERROR_EMULATOR_DOES_NOT_SUPPORT_FILES = \
    'The emulator does not support the file service.'
_ERROR_ACCESS_POLICY = \
    'share_access_policy must be either SignedIdentifier or AccessPolicy ' + \
    'instance'
_ERROR_PARALLEL_NOT_SEEKABLE = 'Parallel operations require a seekable stream.'
_ERROR_VALUE_SHOULD_BE_BYTES = '{0} should be of type bytes.'
_ERROR_VALUE_NONE = '{0} should not be None.'
_ERROR_VALUE_NONE_OR_EMPTY = '{0} should not be None or empty.'
_ERROR_VALUE_NEGATIVE = '{0} should not be negative.'
_ERROR_NO_SINGLE_THREAD_CHUNKING = \
    'To use {0} chunk downloader more than 1 thread must be ' + \
    'used since get_{0}_to_bytes should be called for single threaded ' + \
    '{0} downloads.'
_ERROR_START_END_NEEDED_FOR_MD5 = \
    'Both end_range and start_range need to be specified ' + \
    'for getting content MD5.'
_ERROR_RANGE_TOO_LARGE_FOR_MD5 = \
    'Getting content MD5 for a range greater than 4MB ' + \
    'is not supported.'

def _dont_fail_on_exist(error):
    ''' don't throw exception if the resource exists.
    This is called by create_* APIs with fail_on_exist=False'''
    if isinstance(error, AzureConflictHttpError):
        return False
    else:
        raise error


def _dont_fail_not_exist(error):
    ''' don't throw exception if the resource doesn't exist.
    This is called by create_* APIs with fail_on_exist=False'''
    if isinstance(error, AzureMissingResourceHttpError):
        return False
    else:
        raise error


def _general_error_handler(http_error):
    ''' Simple error handler for azure.'''
    message = str(http_error)
    if http_error.respbody is not None:
        message += '\n' + http_error.respbody.decode('utf-8-sig')
    raise AzureHttpError(message, http_error.status)


def _validate_type_bytes(param_name, param):
    if not isinstance(param, bytes):
        raise TypeError(_ERROR_VALUE_SHOULD_BE_BYTES.format(param_name))


def _validate_not_none(param_name, param):
    if param is None:
        raise ValueError(_ERROR_VALUE_NONE.format(param_name))