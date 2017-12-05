# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Help functions to extract storage account, container name, blob name and other information from
container and/or blob URL.
"""


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class StorageResourceIdentifier(object):
    def __init__(self, cloud, moniker):
        self.is_valid = False
        self.account_name = None
        self.container = None
        self.blob = None
        self.share = None
        self.directory = None
        self.filename = None
        self.snapshot = None
        self.sas_token = None

        from six.moves.urllib.parse import urlparse  # pylint: disable=import-error
        url = urlparse(moniker)

        self._is_url = (url.scheme == 'http' or url.scheme == 'https')
        if not self._is_url:
            return

        if url.path is None:
            return

        self.account_name, type_name = url.netloc[:0 - len(cloud.suffixes.storage_endpoint) - 1]\
            .split('.', 2)

        if type_name == 'blob':
            self.container, self.blob = self._separate_path_l(url.path)
        elif type_name == 'file':
            self.share, file_path = self._separate_path_l(url.path)
            self.directory, self.filename = self._separate_path_r(file_path)
            if self.filename is None:
                self.filename = self.directory
                self.directory = ''
        else:
            self.account_name = None

        if 'snapshot=' not in url.query:
            self.sas_token = url.query
        else:
            parts = url.query.split('&')
            for p in parts:
                if p.startswith('snapshot='):
                    parts.remove(p)
                    self.snapshot = p[9:]
                self.sas_token = '&'.join(parts)

    @classmethod
    def _separate_path_l(cls, path):
        return cls._separate_path(path, lambda p: p.find('/'))

    @classmethod
    def _separate_path_r(cls, path):
        return cls._separate_path(path, lambda p: p.rfind('/'))

    @classmethod
    def _separate_path(cls, path, find_method):
        if path is None:
            return None, None

        path = path.lstrip('/')
        if not path:
            return None, None

        idx = find_method(path)
        if idx == -1:
            return path, None

        return path[:idx], path[idx + 1:]

    def is_url(self):
        return self._is_url
