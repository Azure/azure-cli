# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Help functions to extract storage account, container name, blob name and other information from
container and/or blob URL.
"""

from collections import namedtuple
from azure.cli.core._profile import CLOUD

StorageUrlDescription = namedtuple('StorageUrlDescription',
                                   ['account', 'container', 'blob', 'snapshot'])


def parse_storage_url(url):
    """Extract information from a container/blob url path"""

    def _parse_blob_path(path):
        if path is None:
            return None, None

        path = path.lstrip('/')
        if len(path) == 0:
            return None, None

        idx = path.find('/')
        if idx == -1:
            return path, None
        else:
            return path[:idx], path[idx + 1:]

    if url is None:
        raise ValueError('parameter url is None')

    account_name = None
    container = None
    blob = None
    snapshot = None

    from six.moves.urllib.parse import urlparse #pylint: disable=import-error

    parsed_url = urlparse(url)
    if not parsed_url.scheme == 'http' and not parsed_url.scheme == 'https':
        # the source string is not a url, regards it as a container name
        container = url
    else:
        container, blob = _parse_blob_path(parsed_url.path)
        if container is None:
            raise ValueError('Failed to parse container name from the URL {}'.format(url))

        blob_suffix = '.blob.%s' % CLOUD.suffixes.storage_endpoint
        if parsed_url.netloc.endswith(blob_suffix):
            # it is not a custom domain
            account_name = parsed_url.netloc[:len(parsed_url.netloc) - len(blob_suffix)]

    if parsed_url.query:
        q = parsed_url.query
        i = q.find('snapshot=')
        if i != -1:
            q = q[i:]
            j = q.find('&')
            if j == -1:
                snapshot = q
            else:
                snapshot = q[:j]

    return StorageUrlDescription(account_name, container, blob, snapshot)
