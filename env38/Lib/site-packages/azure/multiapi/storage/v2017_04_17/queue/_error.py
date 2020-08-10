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
import sys

from ..common._error import (
    _validate_type_bytes,
)

_ERROR_MESSAGE_SHOULD_BE_UNICODE = 'message should be of type unicode.'
_ERROR_MESSAGE_SHOULD_BE_STR = 'message should be of type str.'
_ERROR_MESSAGE_NOT_BASE64 = 'message is not a valid base64 value.'
_ERROR_MESSAGE_NOT_ENCRYPTED = 'Message was not encrypted.'

def _validate_message_type_text(param):
    if sys.version_info < (3,):
        if not isinstance(param, unicode):
            raise TypeError(_ERROR_MESSAGE_SHOULD_BE_UNICODE)
    else:
        if not isinstance(param, str):
            raise TypeError(_ERROR_MESSAGE_SHOULD_BE_STR)


def _validate_message_type_bytes(param):
    _validate_type_bytes('message', param)
