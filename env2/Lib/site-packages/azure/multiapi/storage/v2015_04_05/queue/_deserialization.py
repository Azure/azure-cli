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
from dateutil import parser
try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

from .models import (
    Queue,
    QueueMessage,
)
from ..models import (
    _list,
)
from .._deserialization import (
    _int_to_str,
    _parse_response_for_dict,
    _parse_metadata,
)

def _parse_metadata_and_message_count(response):
    '''
    Extracts approximate messages count header.
    '''
    metadata = _parse_metadata(response)

    headers = _parse_response_for_dict(response)
    metadata.approximate_message_count = _int_to_str(headers.get('x-ms-approximate-messages-count'))

    return metadata

def _parse_queue_message_from_headers(response):
    '''
    Extracts pop receipt and time next visible from headers.
    '''
    headers = _parse_response_for_dict(response)

    message = QueueMessage()
    message.pop_receipt = headers.get('x-ms-popreceipt')
    message.time_next_visible = parser.parse(headers.get('x-ms-time-next-visible'))
    
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
        return response

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

def _convert_xml_to_queue_messages(response, decode_function):
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
        return response

    messages = list()
    list_element = ETree.fromstring(response.body)

    for message_element in list_element.findall('QueueMessage'):
        message = QueueMessage()

        message.id = message_element.findtext('MessageId')
        message.dequeue_count = message_element.findtext('DequeueCount')

        message.content = decode_function(message_element.findtext('MessageText'))

        message.insertion_time = parser.parse(message_element.findtext('InsertionTime'))
        message.expiration_time = parser.parse(message_element.findtext('ExpirationTime'))
        
        message.pop_receipt = message_element.findtext('PopReceipt')

        time_next_visible = message_element.find('TimeNextVisible')
        if time_next_visible is not None:
            message.time_next_visible = parser.parse(time_next_visible.text)

        # Add message to list
        messages.append(message)

    return messages