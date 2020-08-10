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
from azure.common import (
    AzureException,
    AzureHttpError,
)

from ._error import (
    _ERROR_ATTRIBUTE_MISSING,
)


class AzureBatchValidationError(AzureException):
    '''
    Indicates that a batch operation cannot proceed due to invalid input.

    :ivar str message: 
        A detailed error message indicating the reason for the failure. 
    '''


class AzureBatchOperationError(AzureHttpError):
    '''
    Indicates that a batch operation failed.
    
    :ivar str message: 
        A detailed error message indicating the index of the batch 
        request which failed and the reason for the failure. For example, 
        '0:One of the request inputs is out of range.' indicates the 0th batch 
        request failed as one of its property values was out of range.
    :ivar int status_code: 
        The HTTP status code of the batch request. For example, 400.
    :ivar str batch_code: 
        The batch status code. For example, 'OutOfRangeInput'.
    '''

    def __init__(self, message, status_code, batch_code):
        super(AzureBatchOperationError, self).__init__(message, status_code)
        self.code = batch_code


class Entity(dict):
    '''
    An entity object. Can be accessed as a dict or as an obj. The attributes of 
    the entity will be created dynamically. For example, the following are both 
    valid::
        entity = Entity()
        entity.a = 'b'
        entity['x'] = 'y'
    '''

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(_ERROR_ATTRIBUTE_MISSING.format('Entity', name))

    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(_ERROR_ATTRIBUTE_MISSING.format('Entity', name))

    def __dir__(self):
        return dir({}) + list(self.keys())


class EntityProperty(object):
    '''
    An entity property. Used to explicitly set :class:`~EdmType` when necessary. 
    
    Values which require explicit typing are GUID, INT32, and BINARY. Other EdmTypes
    may be explicitly create as EntityProperty objects but need not be. For example, 
    the below with both create STRING typed properties on the entity::
        entity = Entity()
        entity.a = 'b'
        entity.x = EntityProperty(EdmType.STRING, 'y')
    '''

    def __init__(self, type=None, value=None, encrypt=False):
        '''
        Represents an Azure Table. Returned by list_tables.

        :param str type: The type of the property.
        :param EdmType value: The value of the property.
        :param bool encrypt: Indicates whether or not the property should be encrypted.
        '''
        self.type = type
        self.value = value
        self.encrypt = encrypt


class Table(object):
    '''
    Represents an Azure Table. Returned by list_tables.

    :ivar str name: The name of the table.
    '''
    pass


class TablePayloadFormat(object):
    '''
    Specifies the accepted content type of the response payload. More information
    can be found here: https://msdn.microsoft.com/en-us/library/azure/dn535600.aspx
    '''

    JSON_NO_METADATA = 'application/json;odata=nometadata'
    '''Returns no type information for the entity properties.'''

    JSON_MINIMAL_METADATA = 'application/json;odata=minimalmetadata'
    '''Returns minimal type information for the entity properties.'''

    JSON_FULL_METADATA = 'application/json;odata=fullmetadata'
    '''Returns minimal type information for the entity properties plus some extra odata properties.'''


class EdmType(object):
    '''
    Used by :class:`~.EntityProperty` to represent the type of the entity property 
    to be stored by the Table service.
    '''

    BINARY = 'Edm.Binary'
    ''' Represents byte data. Must be specified. '''

    INT64 = 'Edm.Int64'
    ''' Represents a number between -(2^31) and 2^31. This is the default type for Python numbers. '''

    GUID = 'Edm.Guid'
    ''' Represents a GUID. Must be specified. '''

    DATETIME = 'Edm.DateTime'
    ''' Represents a date. This type will be inferred for Python datetime objects. '''

    STRING = 'Edm.String'
    ''' Represents a string. This type will be inferred for Python strings. '''

    INT32 = 'Edm.Int32'
    ''' Represents a number between -(2^15) and 2^15. Must be specified or numbers will default to INT64. '''

    DOUBLE = 'Edm.Double'
    ''' Represents a double. This type will be inferred for Python floating point numbers. '''

    BOOLEAN = 'Edm.Boolean'
    ''' Represents a boolean. This type will be inferred for Python bools. '''


class TablePermissions(object):
    '''
    TablePermissions class to be used with the :func:`~azure.storage.table.tableservice.TableService.generate_table_shared_access_signature`
    method and for the AccessPolicies used with :func:`~azure.storage.table.tableservice.TableService.set_table_acl`.

    :ivar TablePermissions TablePermissions.QUERY: Get entities and query entities.
    :ivar TablePermissions TablePermissions.ADD: Add entities.
    :ivar TablePermissions TablePermissions.UPDATE: Update entities.
    :ivar TablePermissions TablePermissions.DELETE: Delete entities.
    '''

    def __init__(self, query=False, add=False, update=False, delete=False, _str=None):
        '''
        :param bool query:
            Get entities and query entities.
        :param bool add:
            Add entities. Add and Update permissions are required for upsert operations.
        :param bool update:
            Update entities. Add and Update permissions are required for upsert operations.
        :param bool delete: 
            Delete entities.
        :param str _str: 
            A string representing the permissions.
        '''
        if not _str:
            _str = ''
        self.query = query or ('r' in _str)
        self.add = add or ('a' in _str)
        self.update = update or ('u' in _str)
        self.delete = delete or ('d' in _str)

    def __or__(self, other):
        return TablePermissions(_str=str(self) + str(other))

    def __add__(self, other):
        return TablePermissions(_str=str(self) + str(other))

    def __str__(self):
        return (('r' if self.query else '') +
                ('a' if self.add else '') +
                ('u' if self.update else '') +
                ('d' if self.delete else ''))


TablePermissions.QUERY = TablePermissions(query=True)
TablePermissions.ADD = TablePermissions(add=True)
TablePermissions.UPDATE = TablePermissions(update=True)
TablePermissions.DELETE = TablePermissions(delete=True)
