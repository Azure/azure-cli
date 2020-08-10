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
    Share,
    Directory,
    File,
    Handle,
    FileProperties,
    FileRange,
    ShareProperties,
    DirectoryProperties,
)
from ..common.models import (
    _list,
)
from ..common._deserialization import (
    _parse_properties,
    _parse_metadata,
)
from ..common._error import _validate_content_match
from ..common._common_conversion import (
    _get_content_md5,
    _to_str,
)


def _parse_snapshot_share(response, name):
    '''
    Extracts snapshot return header.
    '''
    snapshot = response.headers.get('x-ms-snapshot')

    return _parse_share(response, name, snapshot)


def _parse_share(response, name, snapshot=None):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, ShareProperties)
    return Share(name, props, metadata, snapshot)


def _parse_directory(response, name):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, DirectoryProperties)
    return Directory(name, props, metadata)


def _parse_file(response, name, validate_content=False):
    if response is None:
        return None

    metadata = _parse_metadata(response)
    props = _parse_properties(response, FileProperties)

    # For range gets, only look at 'x-ms-content-md5' for overall MD5
    content_settings = getattr(props, 'content_settings')
    if 'content-range' in response.headers:
        if 'x-ms-content-md5' in response.headers:
            setattr(content_settings, 'content_md5', _to_str(response.headers['x-ms-content-md5']))
        else:
            delattr(content_settings, 'content_md5')

    if validate_content:
        computed_md5 = _get_content_md5(response.body)
        _validate_content_match(response.headers['content-md5'], computed_md5)

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
          <Snapshot>date-time-value</Snapshot>
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
        return None

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

        # Snapshot
        share.snapshot = share_element.findtext('Snapshot')

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
    <EnumerationResults ServiceEndpoint="https://myaccount.file.core.windows.net/" ShareName="myshare" DirectoryPath="directory-path">
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
        return None

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


def _convert_xml_to_handles(response):
    """
    <?xml version="1.0" encoding="utf-8"?>
    <EnumerationResults>
        <Entries>
            <Handle>
                <HandleId>21123954401</HandleId>
                <Path />
                <FileId>0</FileId>
                <ParentId>0</ParentId>
                <SessionId>9385737614310506553</SessionId>
                <ClientIp>167.220.2.92:27553</ClientIp>
                <OpenTime>Fri, 03 May 2019 05:59:43 GMT</OpenTime>
            </Handle>
            ...
        </Entries>
        <NextMarker />
    </EnumerationResults>'
    """
    if response is None or response.body is None:
        return None

    entries = _list()
    list_element = ETree.fromstring(response.body)

    # Set next marker
    next_marker = list_element.findtext('NextMarker') or None
    setattr(entries, 'next_marker', next_marker)

    handles_list_element = list_element.find('Entries')

    for handle_element in handles_list_element.findall('Handle'):
        # Name element
        handle = Handle()
        handle.handle_id = handle_element.findtext('HandleId')
        handle.path = handle_element.findtext('Path')
        handle.file_id = handle_element.findtext('FileId')
        handle.parent_id = handle_element.findtext('ParentId')
        handle.session_id = handle_element.findtext('SessionId')
        handle.client_ip = handle_element.findtext('ClientIp')
        handle.open_time = parser.parse(handle_element.findtext('OpenTime'))

        last_connect_time_string = handle_element.findtext('LastReconnectTime')
        if last_connect_time_string is not None:
            handle.last_reconnect_time = parser.parse(last_connect_time_string)

        # Add file to list
        entries.append(handle)

    return entries


def _parse_close_handle_response(response):
    if response is None or response.body is None:
        return 0

    results = _list()
    results.append(int(response.headers['x-ms-number-of-handles-closed']))

    next_marker = None if 'x-ms-marker' not in response.headers else response.headers['x-ms-marker']
    setattr(results, 'next_marker', next_marker)
    return results


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
        return None

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
       <ShareUsageBytes>15</ShareUsageBytes>
    </ShareStats>
    '''
    if response is None or response.body is None:
        return None

    share_stats_element = ETree.fromstring(response.body)
    return int(share_stats_element.findtext('ShareUsageBytes'))
