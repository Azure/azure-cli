# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
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
