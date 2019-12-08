# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import uuid
import azure.cli.command_modules.appconfig._azconfig.constants as constants


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes

class KeyValue(object):
    '''
    Key value class.

    :ivar str key:
        Key of the entry.
    :ivar str value:
        Value of the entry.
    :ivar str label:
        Label of the entry.
    :ivar dict[str, str] tags:
        Dictionary of tags of the entry.
    :ivar str content_type:
        Content type of the entry.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar bool locked:
        Represents whether the key value entry is locked.
    :ivar datetime last_modified:
        A datetime object representing the last time the key was modified.
    '''

    def __init__(self, key, value=None, label=None, tags=None, content_type=None):
        self.key = key
        self.value = value
        self.label = label
        self.tags = tags
        self.content_type = content_type
        self.etag = None
        self.last_modified = None
        self.locked = None

    def __str__(self):
        return "\nKey: " + self.key + \
               "\nValue: " + self.value + \
               "\nLabel: " + (self.label if self.label else '') + \
               "\netag: " + self.etag + \
               "\nLast Modified: " + self.last_modified + \
               "\nContent Type: " + self.content_type + \
               "\nTags: " + (str(self.tags) if self.tags else '')


class QueryFields(Enum):
    KEY = 0x001
    LABEL = 0x002
    VALUE = 0x004
    CONTENT_TYPE = 0x008
    ETAG = 0x010
    LAST_MODIFIED = 0x020
    LOCKED = 0x040
    TAGS = 0x080
    ALL = KEY | LABEL | VALUE | CONTENT_TYPE | ETAG | LAST_MODIFIED | LOCKED | TAGS


class QueryKeyValueOptions(object):
    '''
    Query options for retriving the key-value

    :ivar str label:
        Label of the key-value entry.
    :ivar datetime query_datetime:
        A datetime object representing a timestamp when the request is going to hit.
    :ivar list of QueryFields:
        Client side filter of the query.
    :ivar str client_request_id:
        A request ID that, if provided, can be used to help track the operation.
    :ivar string correlation_request_id:
        An ID that can be used to correlate the request with a more general operation.
    '''

    empty_label = '\\0'

    def __init__(self,
                 label=empty_label,
                 query_datetime=None,
                 fields=None,
                 client_request_id=None,
                 correlation_request_id=None):
        self.label = label
        self.query_datetime = query_datetime
        self.fields = fields
        self.client_request_id = str(
            uuid.uuid4()) if client_request_id is None else client_request_id
        self.correlation_request_id = str(
            uuid.uuid4()) if correlation_request_id is None else correlation_request_id


class QueryKeyValueCollectionOptions(object):
    '''
    Query options for retriving the key-values

    :ivar str key_filter:
        Key of the key-value entry
    :ivar str label_filter:
        Label of the key value entry.
    :ivar datetime query_datetime:
        A datetime object representing a timestamp when the request is going to hit.
    :ivar list of QueryFields:
        Client side filter of the query.
    :ivar str client_request_id:
        A request ID that, if provided, can be used to help track the operation.
    :ivar string correlation_request_id:
        An ID that can be used to correlate the request with a more general operation.
    '''

    any_key = '*'
    any_label = '*'
    empty_label = '\\0'

    def __init__(self,
                 key_filter=any_key,
                 label_filter=any_label,
                 query_datetime=None,
                 fields=None,
                 client_request_id=None,
                 correlation_request_id=None):
        self.key_filter = key_filter
        self.label_filter = label_filter
        self.query_datetime = query_datetime
        self.fields = fields
        self.client_request_id = str(
            uuid.uuid4()) if client_request_id is None else client_request_id
        self.correlation_request_id = str(
            uuid.uuid4()) if correlation_request_id is None else correlation_request_id


class ModifyKeyValueOptions(object):
    '''
    Options for modifying key-value

    :ivar string client_request_id:
        A request ID that, if provided, can be used to help track the operation.
    :ivar string correlation_request_id:
        An ID that can be used to correlate the request with a more general operation.
    '''

    empty_label = '\\0'

    def __init__(self, client_request_id=None, correlation_request_id=None):
        self.client_request_id = str(
            uuid.uuid4()) if client_request_id is None else client_request_id
        self.correlation_request_id = str(
            uuid.uuid4()) if correlation_request_id is None else correlation_request_id


class ClientOptions(object):
    '''
    Options for customizing Azconfig client

    :ivar string user_agent:
        User agent request header.
    :ivar int max_retries
        Maximum retry times for requests
    :ivar float max_retry_wait_time
        Maximum retry wait time for requests in seconds
    '''

    def __init__(self, user_agent=None, max_retries=None, max_retry_wait_time=None):
        self.user_agent = "AzconfigClient/{0}/CLI".format(
            constants.Versions.SDKVersion) if user_agent is None else user_agent
        self.max_retries = 9 if max_retries is None else max_retries
        self.max_retry_wait_time = 30 if max_retry_wait_time is None else max_retry_wait_time
