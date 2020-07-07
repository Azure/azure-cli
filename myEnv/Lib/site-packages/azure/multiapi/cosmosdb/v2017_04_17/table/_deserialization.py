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

from dateutil import parser

if sys.version_info < (3,):
    from urllib2 import quote as url_quote
else:
    from urllib.parse import quote as url_quote
from json import (
    loads,
)
from ..common._http import HTTPResponse
from azure.common import (
    AzureException,
)
from ..common._common_conversion import (
    _decode_base64_to_bytes,
)
from ..common._error import (
    _ERROR_DECRYPTION_FAILURE,
    _validate_decryption_required,
)
from ._error import (
    _ERROR_TYPE_NOT_SUPPORTED,
    _ERROR_INVALID_PROPERTY_RESOLVER,
)
from .models import (
    Entity,
    EntityProperty,
    Table,
    EdmType,
    AzureBatchOperationError,
)
from ..common.models import (
    _list,
)
from ._encryption import (
    _decrypt_entity,
    _extract_encryption_metadata,
)


def _get_continuation_from_response_headers(response):
    marker = {}
    for name, value in response.headers.items():
        if name.startswith('x-ms-continuation'):
            marker[name[len('x-ms-continuation') + 1:]] = value
    return marker


# Tables of conversions to and from entity types.  We support specific
# datatypes, and beyond that the user can use an EntityProperty to get
# custom data type support.

def _from_entity_binary(value):
    return EntityProperty(EdmType.BINARY, _decode_base64_to_bytes(value))


def _from_entity_int32(value):
    return EntityProperty(EdmType.INT32, int(value))


def _from_entity_datetime(value):
    # Note that Azure always returns UTC datetime, and dateutil parser
    # will set the tzinfo on the date it returns
    return parser.parse(value)


_EDM_TYPES = [EdmType.BINARY, EdmType.INT64, EdmType.GUID, EdmType.DATETIME,
              EdmType.STRING, EdmType.INT32, EdmType.DOUBLE, EdmType.BOOLEAN]

_ENTITY_TO_PYTHON_CONVERSIONS = {
    EdmType.BINARY: _from_entity_binary,
    EdmType.INT32: _from_entity_int32,
    EdmType.INT64: int,
    EdmType.DOUBLE: float,
    EdmType.DATETIME: _from_entity_datetime,
}


def _convert_json_response_to_entity(response, property_resolver, require_encryption,
                                     key_encryption_key, key_resolver):
    '''
    :param bool require_encryption:
        If set, will enforce that the retrieved entity is encrypted and decrypt it.
    :param object key_encryption_key:
        The user-provided key-encryption-key. Must implement the following methods:
        unwrap_key(key, algorithm)--returns the unwrapped form of the specified symmetric key using the 
        string-specified algorithm.
        get_kid()--returns a string key id for this key-encryption-key.
     :param function key_resolver(kid):
        The user-provided key resolver. Uses the kid string to return a key-encryption-key implementing
        the interface defined above.
    '''
    if response is None or response.body is None:
        return None

    root = loads(response.body.decode('utf-8'))
    return _decrypt_and_deserialize_entity(root, property_resolver, require_encryption,
                                           key_encryption_key, key_resolver)


def _convert_json_to_entity(entry_element, property_resolver, encrypted_properties):
    ''' Convert json response to entity.

    The entity format is:
    {
       "Address":"Mountain View",
       "Age":23,
       "AmountDue":200.23,
       "CustomerCode@odata.type":"Edm.Guid",
       "CustomerCode":"c9da6455-213d-42c9-9a79-3e9149a57833",
       "CustomerSince@odata.type":"Edm.DateTime",
       "CustomerSince":"2008-07-10T00:00:00",
       "IsActive":true,
       "NumberOfOrders@odata.type":"Edm.Int64",
       "NumberOfOrders":"255",
       "PartitionKey":"mypartitionkey",
       "RowKey":"myrowkey"
    }
    '''
    entity = Entity()

    properties = {}
    edmtypes = {}
    odata = {}

    for name, value in entry_element.items():
        if name.startswith('odata.'):
            odata[name[6:]] = value
        elif name.endswith('@odata.type'):
            edmtypes[name[:-11]] = value
        else:
            properties[name] = value

    # Partition key is a known property
    partition_key = properties.pop('PartitionKey', None)
    if partition_key:
        entity['PartitionKey'] = partition_key

    # Row key is a known property
    row_key = properties.pop('RowKey', None)
    if row_key:
        entity['RowKey'] = row_key

    # Timestamp is a known property
    timestamp = properties.pop('Timestamp', None)
    if timestamp:
        entity['Timestamp'] = _from_entity_datetime(timestamp)

    for name, value in properties.items():
        mtype = edmtypes.get(name)

        # use the property resolver if present
        if property_resolver:
            # Clients are not expected to resolve these interal fields.
            # This check avoids unexpected behavior from the user-defined 
            # property resolver.
            if not (name == '_ClientEncryptionMetadata1' or name == '_ClientEncryptionMetadata2'):
                mtype = property_resolver(partition_key, row_key,
                                          name, value, mtype)

                # throw if the type returned is not a valid edm type
                if mtype and mtype not in _EDM_TYPES:
                    raise AzureException(_ERROR_TYPE_NOT_SUPPORTED.format(mtype))

        # If the property was encrypted, supercede the results of the resolver and set as binary
        if encrypted_properties is not None and name in encrypted_properties:
            mtype = EdmType.BINARY

        # Add type for Int32
        if type(value) is int:
            mtype = EdmType.INT32

        # no type info, property should parse automatically
        if not mtype:
            entity[name] = value
        else:  # need an object to hold the property
            conv = _ENTITY_TO_PYTHON_CONVERSIONS.get(mtype)
            if conv is not None:
                try:
                    property = conv(value)
                except Exception as e:
                    # throw if the type returned by the property resolver
                    # cannot be used in the conversion
                    if property_resolver:
                        raise AzureException(
                            _ERROR_INVALID_PROPERTY_RESOLVER.format(name, value, mtype))
                    else:
                        raise e
            else:
                property = EntityProperty(mtype, value)
            entity[name] = property

    # extract etag from entry
    etag = odata.get('etag')
    if timestamp:
        etag = 'W/"datetime\'' + url_quote(timestamp) + '\'"'
    entity['etag'] = etag

    return entity


def _convert_json_response_to_tables(response):
    ''' Converts the response to tables class.
    '''
    if response is None or response.body is None:
        return None

    tables = _list()

    continuation = _get_continuation_from_response_headers(response)
    tables.next_marker = continuation.get('nexttablename')

    root = loads(response.body.decode('utf-8'))

    if 'TableName' in root:
        table = Table()
        table.name = root['TableName']
        tables.append(table)
    else:
        for element in root['value']:
            table = Table()
            table.name = element['TableName']
            tables.append(table)

    return tables


def _convert_json_response_to_entities(response, property_resolver, require_encryption,
                                       key_encryption_key, key_resolver):
    ''' Converts the response to tables class.
    '''
    if response is None or response.body is None:
        return None

    entities = _list()

    entities.next_marker = _get_continuation_from_response_headers(response)

    root = loads(response.body.decode('utf-8'))

    for entity in root['value']:
        entity = _decrypt_and_deserialize_entity(entity, property_resolver, require_encryption,
                                                 key_encryption_key, key_resolver)
        entities.append(entity)

    return entities


def _decrypt_and_deserialize_entity(entity, property_resolver, require_encryption,
                                    key_encryption_key, key_resolver):
    try:
        _validate_decryption_required(require_encryption, key_encryption_key,
                                      key_resolver)
        entity_iv, encrypted_properties, content_encryption_key, isJavaV1 = None, None, None, False
        if (key_encryption_key is not None) or (key_resolver is not None):
            entity_iv, encrypted_properties, content_encryption_key, isJavaV1 = \
                _extract_encryption_metadata(entity, require_encryption, key_encryption_key, key_resolver)
    except:
        raise AzureException(_ERROR_DECRYPTION_FAILURE)

    entity = _convert_json_to_entity(entity, property_resolver, encrypted_properties)

    if entity_iv is not None and encrypted_properties is not None and \
                    content_encryption_key is not None:
        try:
            entity = _decrypt_entity(entity, encrypted_properties, content_encryption_key,
                                     entity_iv, isJavaV1)
        except:
            raise AzureException(_ERROR_DECRYPTION_FAILURE)

    return entity


def _extract_etag(response):
    ''' Extracts the etag from the response headers. '''
    if response and response.headers:
        return response.headers.get('etag')

    return None


def _parse_batch_response(response):
    if response is None or response.body is None:
        return None

    parts = response.body.split(b'--changesetresponse_')

    responses = []
    for part in parts:
        httpLocation = part.find(b'HTTP/')
        if httpLocation > 0:
            response_part = _parse_batch_response_part(part[httpLocation:])
            if response_part.status >= 300:
                _parse_batch_error(response_part)
            responses.append(_extract_etag(response_part))

    return responses


def _parse_batch_response_part(part):
    lines = part.splitlines()

    # First line is the HTTP status/reason
    status, _, reason = lines[0].partition(b' ')[2].partition(b' ')

    # Followed by headers and body
    headers = {}
    body = b''
    isBody = False
    for line in lines[1:]:
        if line == b'' and not isBody:
            isBody = True
        elif isBody:
            body += line
        else:
            headerName, _, headerVal = line.partition(b': ')
            headers[headerName.lower().decode("utf-8")] = headerVal.decode("utf-8")

    return HTTPResponse(int(status), reason.strip(), headers, body)


def _parse_batch_error(part):
    doc = loads(part.body.decode('utf-8'))

    code = ''
    message = ''
    error = doc.get('odata.error')
    if error:
        code = error.get('code')
        if error.get('message'):
            message = error.get('message').get('value')

    raise AzureBatchOperationError(message, part.status, code)
