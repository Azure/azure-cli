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
from ._error import (
    _ERROR_INCORRECT_PARTITION_KEY_IN_BATCH,
    _ERROR_DUPLICATE_ROW_KEY_IN_BATCH,
    _ERROR_TOO_MANY_ENTITIES_IN_BATCH,
)
from .models import (
    AzureBatchValidationError,
)
from ._request import (
    _insert_entity,
    _update_entity,
    _merge_entity,
    _delete_entity,
    _insert_or_replace_entity,
    _insert_or_merge_entity,
)

class TableBatch(object):

    '''
    This is the class that is used for batch operation for storage table service.

    The Table service supports batch transactions on entities that are in the 
    same table and belong to the same partition group. Multiple operations are 
    supported within a single transaction. The batch can include at most 100 
    entities, and its total payload may be no more than 4 MB in size.
    '''

    def __init__(self):
        self._requests = []
        self._partition_key = None
        self._row_keys = []

    def insert_entity(self, entity):
        '''
        Adds an insert entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.insert_entity` for more 
        information on inserts.
        
        The operation will not be executed until the batch is committed.

        :param entity:
            The entity to insert. Could be a dict or an entity object. 
            Must contain a PartitionKey and a RowKey.
        :type entity: a dict or :class:`azure.storage.table.models.Entity`
        '''
        request = _insert_entity(entity)
        self._add_to_batch(entity['PartitionKey'], entity['RowKey'], request)

    def update_entity(self, entity, if_match='*'):
        '''
        Adds an update entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.update_entity` for more 
        information on updates.
        
        The operation will not be executed until the batch is committed.

        :param entity:
            The entity to update. Could be a dict or an entity object. 
            Must contain a PartitionKey and a RowKey.
        :type entity: a dict or :class:`azure.storage.table.models.Entity`
        :param str if_match:
            The client may specify the ETag for the entity on the 
            request in order to compare to the ETag maintained by the service 
            for the purpose of optimistic concurrency. The update operation 
            will be performed only if the ETag sent by the client matches the 
            value maintained by the server, indicating that the entity has 
            not been modified since it was retrieved by the client. To force 
            an unconditional update, set If-Match to the wildcard character (*).
        '''
        request = _update_entity(entity, if_match)
        self._add_to_batch(entity['PartitionKey'], entity['RowKey'], request)

    def merge_entity(self, entity, if_match='*'):
        '''
        Adds a merge entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.merge_entity` for more 
        information on merges.
        
        The operation will not be executed until the batch is committed.

        :param entity:
            The entity to merge. Could be a dict or an entity object. 
            Must contain a PartitionKey and a RowKey.
        :type entity: a dict or :class:`azure.storage.table.models.Entity`
        :param str if_match:
            The client may specify the ETag for the entity on the 
            request in order to compare to the ETag maintained by the service 
            for the purpose of optimistic concurrency. The merge operation 
            will be performed only if the ETag sent by the client matches the 
            value maintained by the server, indicating that the entity has 
            not been modified since it was retrieved by the client. To force 
            an unconditional merge, set If-Match to the wildcard character (*).
        '''
        request = _merge_entity(entity, if_match)
        self._add_to_batch(entity['PartitionKey'], entity['RowKey'], request)

    def delete_entity(self, partition_key, row_key,
                      if_match='*'):
        '''
        Adds a delete entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.delete_entity` for more 
        information on deletes.

        The operation will not be executed until the batch is committed.

        :param str partition_key:
            The PartitionKey of the entity.
        :param str row_key:
            The RowKey of the entity.
        :param str if_match:
            The client may specify the ETag for the entity on the 
            request in order to compare to the ETag maintained by the service 
            for the purpose of optimistic concurrency. The delete operation 
            will be performed only if the ETag sent by the client matches the 
            value maintained by the server, indicating that the entity has 
            not been modified since it was retrieved by the client. To force 
            an unconditional delete, set If-Match to the wildcard character (*).
        '''
        request = _delete_entity(partition_key, row_key, if_match)
        self._add_to_batch(partition_key, row_key, request)

    def insert_or_replace_entity(self, entity):
        '''
        Adds an insert or replace entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.insert_or_replace_entity` for more 
        information on insert or replace operations.

        The operation will not be executed until the batch is committed.

        :param entity:
            The entity to insert or replace. Could be a dict or an entity object. 
            Must contain a PartitionKey and a RowKey.
        :type entity: a dict or :class:`azure.storage.table.models.Entity`
       '''
        request = _insert_or_replace_entity(entity)
        self._add_to_batch(entity['PartitionKey'], entity['RowKey'], request)

    def insert_or_merge_entity(self, entity):
        '''
        Adds an insert or merge entity operation to the batch. See 
        :func:`~azure.storage.table.tableservice.TableService.insert_or_merge_entity` for more 
        information on insert or merge operations.

        The operation will not be executed until the batch is committed.

        :param entity:
            The entity to insert or merge. Could be a dict or an entity object. 
            Must contain a PartitionKey and a RowKey.
        :type entity: a dict or :class:`azure.storage.table.models.Entity`
        '''
        request = _insert_or_merge_entity(entity)
        self._add_to_batch(entity['PartitionKey'], entity['RowKey'], request)

    def _add_to_batch(self, partition_key, row_key, request):
        '''
        Validates batch-specific rules.
        
        :param str partition_key:
            PartitionKey of the entity.
        :param str row_key:
            RowKey of the entity.
        :param request:
            the request to insert, update or delete entity
        '''
        # All same partition keys
        if self._partition_key:
            if self._partition_key != partition_key:
                raise AzureBatchValidationError(_ERROR_INCORRECT_PARTITION_KEY_IN_BATCH)
        else:
            self._partition_key = partition_key

        # All different row keys
        if row_key in self._row_keys:
            raise AzureBatchValidationError(_ERROR_DUPLICATE_ROW_KEY_IN_BATCH)
        else:
            self._row_keys.append(row_key)
        
        # 100 entities
        if len(self._requests) >= 100:
            raise AzureBatchValidationError(_ERROR_TOO_MANY_ENTITIES_IN_BATCH)

        # Add the request to the batch
        self._requests.append((row_key, request))