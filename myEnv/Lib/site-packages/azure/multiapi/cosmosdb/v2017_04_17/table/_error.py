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

from ..common._error import (
    _validate_not_none,
    _ERROR_VALUE_NONE_OR_EMPTY,
)

_ERROR_ATTRIBUTE_MISSING = '\'{0}\' object has no attribute \'{1}\''
_ERROR_BATCH_COMMIT_FAIL = 'Batch Commit Fail'
_ERROR_CANNOT_FIND_PARTITION_KEY = 'Cannot find partition key in request.'
_ERROR_CANNOT_FIND_ROW_KEY = 'Cannot find row key in request.'
_ERROR_CANNOT_SERIALIZE_VALUE_TO_ENTITY = \
    'Cannot serialize the specified value ({0}) to an entity.  Please use ' + \
    'an EntityProperty (which can specify custom types), int, str, bool, ' + \
    'or datetime.'
_ERROR_DUPLICATE_ROW_KEY_IN_BATCH = \
    'Row Keys should not be the same in a batch operations'
_ERROR_INCORRECT_PARTITION_KEY_IN_BATCH = \
    'Partition Key should be the same in a batch operations'
_ERROR_INVALID_ENTITY_TYPE = 'The entity must be either in dict format or an entity object.'
_ERROR_INVALID_PROPERTY_RESOLVER = \
    'The specified property resolver returned an invalid type. Name: {0}, Value: {1}, ' + \
    'EdmType: {2}'
_ERROR_PROPERTY_NAME_TOO_LONG = 'The property name exceeds the maximum allowed length.'
_ERROR_TOO_MANY_ENTITIES_IN_BATCH = \
    'Batches may only contain 100 operations'
_ERROR_TOO_MANY_PROPERTIES = 'The entity contains more properties than allowed.'
_ERROR_TYPE_NOT_SUPPORTED = 'Type not supported when sending data to the service: {0}.'
_ERROR_VALUE_TOO_LARGE = '{0} is too large to be cast to type {1}.'
_ERROR_UNSUPPORTED_TYPE_FOR_ENCRYPTION = 'Encryption is only supported for not None strings.'
_ERROR_ENTITY_NOT_ENCRYPTED = 'Entity was not encrypted.'


def _validate_object_has_param(param_name, object):
    if object.get(param_name) is None:
        raise ValueError(_ERROR_VALUE_NONE_OR_EMPTY.format(param_name))


def _validate_entity(entity, encrypt=None):
    # Validate entity exists
    _validate_not_none('entity', entity)

    # Entity inherits from dict, so just validating dict is fine
    if not isinstance(entity, dict):
        raise TypeError(_ERROR_INVALID_ENTITY_TYPE)

    # Validate partition key and row key are present
    _validate_object_has_param('PartitionKey', entity)
    _validate_object_has_param('RowKey', entity)

    # Two properties are added during encryption. Validate sufficient space
    max_properties = 255
    if encrypt:
        max_properties = max_properties - 2

    # Validate there are not more than 255 properties including Timestamp
    if (len(entity) > max_properties) or (len(entity) == max_properties and 'Timestamp' not in entity):
        raise ValueError(_ERROR_TOO_MANY_PROPERTIES)

    # Validate the property names are not too long
    for propname in entity:
        if len(propname) > 255:
            raise ValueError(_ERROR_PROPERTY_NAME_TOO_LONG)
