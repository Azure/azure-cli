# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Help functions to normalize and compare storage URL origins.
Help functions to extract storage account, container name, blob name and other information from
container and/or blob URL.
"""

import re

_HOSTNAME_LABEL_PATTERN = re.compile(r'[A-Za-z0-9-]{1,63}')


def is_valid_hostname_label(name):
    """Return whether `name` is a single DNS hostname label (letters, digits and hyphens only)."""
    return isinstance(name, str) and _HOSTNAME_LABEL_PATTERN.fullmatch(name) is not None


def normalize_url_origin(url):
    from ipaddress import ip_address
    from urllib.parse import urlsplit
    import idna

    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        if scheme not in ('http', 'https') or not hostname:
            return None

        hostname = hostname.rstrip('.')
        if not hostname:
            return None
        try:
            hostname = ip_address(hostname).compressed
        except ValueError:
            hostname = idna.encode(hostname, uts46=True).decode('ascii').lower().rstrip('.')
            if not hostname:
                return None

        port = parsed.port
        if port is None:
            port = 443 if scheme == 'https' else 80
        return scheme, hostname, port
    except (UnicodeError, ValueError):
        return None


def same_url_origin(first_url, second_url):
    first_origin = normalize_url_origin(first_url)
    return first_origin is not None and first_origin == normalize_url_origin(second_url)


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class StorageResourceIdentifier:
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

        from urllib.parse import urlparse
        url = urlparse(moniker)

        self._is_url = (url.scheme == 'http' or url.scheme == 'https')
        if not self._is_url:
            return

        if url.path is None:
            return

        self.account_name, type_name = self._parse_account_and_service(url, cloud.suffixes.storage_endpoint)

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

    @staticmethod
    def _parse_account_and_service(url, storage_endpoint):
        """Extract (account, service) from a `<account>.<blob|file>.<storage_endpoint>` host, or (None, None)."""
        hostname = url.hostname  # lowercased, without userinfo or port
        suffix = '.' + storage_endpoint.lower()
        if not hostname or not hostname.endswith(suffix):
            return None, None

        account_name, _, service = hostname[:-len(suffix)].partition('.')
        if service not in ('blob', 'file') or not is_valid_hostname_label(account_name):
            return None, None

        # keep the account name as written in the URL, since urlparse lowercases the hostname
        raw_account_name = url.netloc.rpartition('@')[2][:len(account_name)]
        if raw_account_name.lower() == account_name and is_valid_hostname_label(raw_account_name):
            account_name = raw_account_name
        return account_name, service

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
