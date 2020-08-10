# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from dateutil import parser

try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

from .models import (
    Queue,
    QueueMessage,
)
from ..common.models import (
    _list,
)
from ..common._deserialization import (
    _to_int,
    _parse_metadata,
)
from ._encryption import (
    _decrypt_queue_message,
)


def _parse_metadata_and_message_count(response):
    '''
    Extracts approximate messages count header.
    '''
    metadata = _parse_metadata(response)
    metadata.approximate_message_count = _to_int(response.headers.get('x-ms-approximate-messages-count'))

    return metadata


def _parse_queue_message_from_headers(response):
    '''
    Extracts pop receipt and time next visible from headers.
    '''
    message = QueueMessage()
    message.pop_receipt = response.headers.get('x-ms-popreceipt')
    message.time_next_visible = parser.parse(response.headers.get('x-ms-time-next-visible'))

    return message


def _convert_xml_to_queues(response):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <EnumerationResults ServiceEndpoint="https://myaccount.queue.core.windows.net/">
      <Prefix>string-value</Prefix>
      <Marker>string-value</Marker>
      <MaxResults>int-value</MaxResults>
      <Queues>
        <Queue>
          <Name>string-value</Name>
          <Metadata>
            <metadata-name>value</metadata-name>
          </Metadata>
        </Queue>
      <NextMarker />
    </EnumerationResults>
    '''
    if response is None or response.body is None:
        return None

    queues = _list()
    list_element = ETree.fromstring(response.body)

    # Set next marker
    next_marker = list_element.findtext('NextMarker') or None
    setattr(queues, 'next_marker', next_marker)

    queues_element = list_element.find('Queues')

    for queue_element in queues_element.findall('Queue'):
        # Name element
        queue = Queue()
        queue.name = queue_element.findtext('Name')

        # Metadata
        metadata_root_element = queue_element.find('Metadata')
        if metadata_root_element is not None:
            queue.metadata = dict()
            for metadata_element in metadata_root_element:
                queue.metadata[metadata_element.tag] = metadata_element.text

        # Add queue to list
        queues.append(queue)

    return queues


def _convert_xml_to_queue_messages(response, decode_function, require_encryption, key_encryption_key, resolver,
                                   content=None):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <QueueMessagesList>
        <QueueMessage>
          <MessageId>string-message-id</MessageId>
          <InsertionTime>insertion-time</InsertionTime>
          <ExpirationTime>expiration-time</ExpirationTime>
          <PopReceipt>opaque-string-receipt-data</PopReceipt>
          <TimeNextVisible>time-next-visible</TimeNextVisible>
          <DequeueCount>integer</DequeueCount>
          <MessageText>message-body</MessageText>
        </QueueMessage>
    </QueueMessagesList>
    '''
    if response is None or response.body is None:
        return None

    messages = list()
    list_element = ETree.fromstring(response.body)

    for message_element in list_element.findall('QueueMessage'):
        message = QueueMessage()

        message.id = message_element.findtext('MessageId')

        dequeue_count = message_element.findtext('DequeueCount')
        if dequeue_count is not None:
            message.dequeue_count = _to_int(dequeue_count)

        # content is not returned for put_message
        if content is not None:
            message.content = content
        else:
            message.content = message_element.findtext('MessageText')
            if (key_encryption_key is not None) or (resolver is not None):
                message.content = _decrypt_queue_message(message.content, require_encryption,
                                                         key_encryption_key, resolver)
            message.content = decode_function(message.content)

        message.insertion_time = parser.parse(message_element.findtext('InsertionTime'))
        message.expiration_time = parser.parse(message_element.findtext('ExpirationTime'))

        message.pop_receipt = message_element.findtext('PopReceipt')

        time_next_visible = message_element.find('TimeNextVisible')
        if time_next_visible is not None:
            message.time_next_visible = parser.parse(time_next_visible.text)

        # Add message to list
        messages.append(message)

    return messages
