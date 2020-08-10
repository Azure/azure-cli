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
import sys
if sys.version_info >= (3,):
    from io import BytesIO
else:
    try:
        from cStringIO import StringIO as BytesIO
    except:
        from StringIO import StringIO as BytesIO

try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree

from xml.sax.saxutils import escape as xml_escape
from .._common_conversion import (
    _str,
)

def _get_path(queue_name=None, include_messages=None, message_id=None):
    '''
    Creates the path to access a queue resource.

    queue_name:
        Name of queue.
    include_messages:
        Whether or not to include messages.
    message_id:
        Message id.
    '''
    if queue_name and include_messages and message_id:
        return '/{0}/messages/{1}'.format(_str(queue_name), message_id)
    if queue_name and include_messages:
        return '/{0}/messages'.format(_str(queue_name))
    elif queue_name:
        return '/{0}'.format(_str(queue_name))
    else:
        return '/'


def _convert_queue_message_xml(message_text, encode_function):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <QueueMessage>
        <MessageText></MessageText>
    </QueueMessage>
    '''
    queue_message_element = ETree.Element('QueueMessage');

    # Enabled
    message_text = encode_function(message_text)
    ETree.SubElement(queue_message_element, 'MessageText').text = message_text

    # Add xml declaration and serialize
    try:
        stream = BytesIO()
        ETree.ElementTree(queue_message_element).write(stream, xml_declaration=True, encoding='utf-8', method='xml')
        output = stream.getvalue()
    finally:
        stream.close()

    return output
