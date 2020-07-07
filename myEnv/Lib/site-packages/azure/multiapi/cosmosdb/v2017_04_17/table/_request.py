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
from ..common._common_conversion import (
    _to_str,
)
from ..common._error import (
    _validate_not_none,
    _validate_encryption_required,
    _validate_encryption_unsupported,
)
from ..common._http import HTTPRequest
from ..common._serialization import (
    _get_request_body,
)
from ._encryption import (
    _encrypt_entity,
)
from ._error import (
    _validate_entity,
)
from ._serialization import (
    _convert_entity_to_json,
    _DEFAULT_ACCEPT_HEADER,
    _DEFAULT_CONTENT_TYPE_HEADER,
    _DEFAULT_PREFER_HEADER,
)


def _get_entity(partition_key, row_key, select, accept):
    '''
    Constructs a get entity request.
    '''
    _validate_not_none('partition_key', partition_key)
    _validate_not_none('row_key', row_key)
    _validate_not_none('accept', accept)
    request = HTTPRequest()
    request.method = 'GET'
    request.headers = {'Accept': _to_str(accept)}
    request.query = {'$select': _to_str(select)}

    return request


def _insert_entity(entity, encryption_required=False,
                   key_encryption_key=None, encryption_resolver=None):
    '''
    Constructs an insert entity request.
    :param entity:
        The entity to insert. Could be a dict or an entity object.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        wrap_key(key)--wraps the specified key using an algorithm of the user's choice.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function(partition_key, row_key, property_name) encryption_resolver:
        A function that takes in an entities partition key, row key, and property name and returns 
        a boolean that indicates whether that property should be encrypted.
    '''
    _validate_entity(entity, key_encryption_key is not None)
    _validate_encryption_required(encryption_required, key_encryption_key)

    request = HTTPRequest()
    request.method = 'POST'
    request.headers = {
        _DEFAULT_CONTENT_TYPE_HEADER[0]: _DEFAULT_CONTENT_TYPE_HEADER[1],
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
        _DEFAULT_PREFER_HEADER[0]: _DEFAULT_PREFER_HEADER[1]
    }
    if key_encryption_key:
        entity = _encrypt_entity(entity, key_encryption_key, encryption_resolver)
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request


def _update_entity(entity, if_match, encryption_required=False,
                   key_encryption_key=None, encryption_resolver=None):
    '''
    Constructs an update entity request.
    :param entity:
        The entity to insert. Could be a dict or an entity object.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        wrap_key(key)--wraps the specified key using an algorithm of the user's choice.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
    :param function(partition_key, row_key, property_name) encryption_resolver:
        A function that takes in an entities partition key, row key, and property name and returns 
        a boolean that indicates whether that property should be encrypted.
    '''
    _validate_not_none('if_match', if_match)
    _validate_entity(entity, key_encryption_key is not None)
    _validate_encryption_required(encryption_required, key_encryption_key)

    request = HTTPRequest()
    request.method = 'PUT'
    request.headers = {
        _DEFAULT_CONTENT_TYPE_HEADER[0]: _DEFAULT_CONTENT_TYPE_HEADER[1],
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
        'If-Match': _to_str(if_match),
    }
    if key_encryption_key:
        entity = _encrypt_entity(entity, key_encryption_key, encryption_resolver)
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request


def _merge_entity(entity, if_match, require_encryption=False, key_encryption_key=None):
    '''
    Constructs a merge entity request.
    '''
    _validate_not_none('if_match', if_match)
    _validate_entity(entity)
    _validate_encryption_unsupported(require_encryption, key_encryption_key)

    request = HTTPRequest()
    request.method = 'MERGE'
    request.headers = {
        _DEFAULT_CONTENT_TYPE_HEADER[0]: _DEFAULT_CONTENT_TYPE_HEADER[1],
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
        'If-Match': _to_str(if_match)
    }
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request


def _delete_entity(partition_key, row_key, if_match):
    '''
     Constructs a delete entity request.
    '''
    _validate_not_none('if_match', if_match)
    _validate_not_none('partition_key', partition_key)
    _validate_not_none('row_key', row_key)
    request = HTTPRequest()
    request.method = 'DELETE'
    request.headers = {
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
        'If-Match': _to_str(if_match)
    }

    return request


def _insert_or_replace_entity(entity, require_encryption=False,
                              key_encryption_key=None, encryption_resolver=None):
    '''
    Constructs an insert or replace entity request.
    '''
    _validate_entity(entity, key_encryption_key is not None)
    _validate_encryption_required(require_encryption, key_encryption_key)

    request = HTTPRequest()
    request.method = 'PUT'
    request.headers = {
        _DEFAULT_CONTENT_TYPE_HEADER[0]: _DEFAULT_CONTENT_TYPE_HEADER[1],
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
    }

    if key_encryption_key:
        entity = _encrypt_entity(entity, key_encryption_key, encryption_resolver)
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request


def _insert_or_merge_entity(entity, require_encryption=False, key_encryption_key=None):
    '''
    Constructs an insert or merge entity request.
    :param entity:
        The entity to insert. Could be a dict or an entity object.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        wrap_key(key)--wraps the specified key using an algorithm of the user's choice.
        get_key_wrap_algorithm()--returns the algorithm used to wrap the specified symmetric key.
        get_kid()--returns a string key id for this key-encryption-key.
    '''
    _validate_entity(entity)
    _validate_encryption_unsupported(require_encryption, key_encryption_key)

    request = HTTPRequest()
    request.method = 'MERGE'
    request.headers = {
        _DEFAULT_CONTENT_TYPE_HEADER[0]: _DEFAULT_CONTENT_TYPE_HEADER[1],
        _DEFAULT_ACCEPT_HEADER[0]: _DEFAULT_ACCEPT_HEADER[1],
    }
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request
