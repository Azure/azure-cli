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
from .._http import HTTPRequest
from .._common_conversion import (
    _to_str,
)
from .._error import (
    _validate_not_none,
)
from .._serialization import (
    _get_request_body,
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
    request.headers = [('Accept', _to_str(accept))]
    request.query = [('$select', _to_str(select))]

    return request

def _insert_entity(entity):
    '''
    Constructs an insert entity request.
    '''
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'POST'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_PREFER_HEADER,
                        _DEFAULT_ACCEPT_HEADER]
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request

def _update_entity(entity, if_match):
    '''
    Constructs an update entity request.
    '''
    _validate_not_none('if_match', if_match)
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'PUT'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_ACCEPT_HEADER,
                        ('If-Match', _to_str(if_match)),]
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request

def _merge_entity(entity, if_match):
    '''
    Constructs a merge entity request.
    '''
    _validate_not_none('if_match', if_match)
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'MERGE'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_ACCEPT_HEADER,
                        ('If-Match', _to_str(if_match))]
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
    request.headers = [_DEFAULT_ACCEPT_HEADER,
                        ('If-Match', _to_str(if_match))]

    return request

def _insert_or_replace_entity(entity):
    '''
    Constructs an insert or replace entity request.
    '''
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'PUT'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_ACCEPT_HEADER]
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request

def _insert_or_merge_entity(entity):
    '''
    Constructs an insert or merge entity request.
    '''
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'MERGE'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_ACCEPT_HEADER]
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request