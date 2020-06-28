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
    Share,
    Directory,
    File,
    FileProperties,
    FileRange,
    ShareProperties,
    DirectoryProperties,
)
from ..models import (
    _list,
)
from .._deserialization import (
    _parse_properties,
    _parse_metadata,
)

def _parse_share(name, response):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, ShareProperties)
    return Share(name, props, metadata)

def _parse_directory(name, response):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, DirectoryProperties)
    return Directory(name, props, metadata)

def _parse_file(name, response):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, FileProperties)
    return File(name, response.body, props, metadata)

def _convert_xml_to_shares(response):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <EnumerationResults AccountName="https://myaccount.file.core.windows.net">
      <Prefix>string-value</Prefix>
      <Marker>string-value</Marker>
      <MaxResults>int-value</MaxResults>
      <Shares>
        <Share>
          <Name>share-name</Name>
          <Properties>
            <Last-Modified>date/time-value</Last-Modified>
            <Etag>etag</Etag>
            <Quota>max-share-size</Quota>
          </Properties>
          <Metadata>
            <metadata-name>value</metadata-name>
          </Metadata>
        </Share>
      </Shares>
      <NextMarker>marker-value</NextMarker>
    </EnumerationResults>
    '''
    if response is None or response.body is None:
        return response

    shares = _list()
    list_element = ETree.fromstring(response.body)
    
    # Set next marker
    next_marker = list_element.findtext('NextMarker') or None
    setattr(shares, 'next_marker', next_marker)

    shares_element = list_element.find('Shares')

    for share_element in shares_element.findall('Share'):
        # Name element
        share = Share()
        share.name = share_element.findtext('Name')

        # Metadata
        metadata_root_element = share_element.find('Metadata')
        if metadata_root_element is not None:
            share.metadata = dict()
            for metadata_element in metadata_root_element:
                share.metadata[metadata_element.tag] = metadata_element.text

        # Properties
        properties_element = share_element.find('Properties')
        share.properties.last_modified = parser.parse(properties_element.findtext('Last-Modified'))
        share.properties.etag = properties_element.findtext('Etag')
        share.properties.quota = int(properties_element.findtext('Quota'))
        
        # Add share to list
        shares.append(share)

    return shares

def _convert_xml_to_directories_and_files(response):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <EnumerationResults ServiceEndpoint="https://myaccount.file.core.windows.net/” ShareName="myshare" DirectoryPath="directory-path">
      <Marker>string-value</Marker>
      <MaxResults>int-value</MaxResults>
      <Entries>
        <File>
          <Name>file-name</Name>
          <Properties>
            <Content-Length>size-in-bytes</Content-Length>
          </Properties>
        </File>
        <Directory>
          <Name>directory-name</Name>
        </Directory>
      </Entries>
      <NextMarker />
    </EnumerationResults>
    '''
    if response is None or response.body is None:
        return response

    entries = _list()
    list_element = ETree.fromstring(response.body)
    
    # Set next marker
    next_marker = list_element.findtext('NextMarker') or None
    setattr(entries, 'next_marker', next_marker)

    entries_element = list_element.find('Entries')

    for file_element in entries_element.findall('File'):
        # Name element
        file = File()
        file.name = file_element.findtext('Name')

        # Properties
        properties_element = file_element.find('Properties')
        file.properties.content_length = int(properties_element.findtext('Content-Length'))
        
        # Add file to list
        entries.append(file)

    for directory_element in entries_element.findall('Directory'):
        # Name element
        directory = Directory()
        directory.name = directory_element.findtext('Name')
        
        # Add directory to list
        entries.append(directory)

    return entries

def _convert_xml_to_ranges(response):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <Ranges>
      <Range>
        <Start>Start Byte</Start>
        <End>End Byte</End>
      </Range>
      <Range>
        <Start>Start Byte</Start>
        <End>End Byte</End>
      </Range>
    </Ranges>
    '''
    if response is None or response.body is None:
        return response

    ranges = list()
    ranges_element = ETree.fromstring(response.body)

    for range_element in ranges_element.findall('Range'):
        # Parse range
        range = FileRange(int(range_element.findtext('Start')), int(range_element.findtext('End')))
        
        # Add range to list
        ranges.append(range)

    return ranges

def _convert_xml_to_share_stats(response):
    '''
    <?xml version="1.0" encoding="utf-8"?>
    <ShareStats>
       <ShareUsage>15</ShareUsage>
    </ShareStats>
    '''
    if response is None or response.body is None:
        return response

    share_stats_element = ETree.fromstring(response.body)
    return int(share_stats_element.findtext('ShareUsage'))