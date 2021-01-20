# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import logging
import os
import time

try:
    import collections.abc as collections
except ImportError:
    import collections

from codecs import open as codecs_open

from knack.log import get_logger

try:
    t_JSONDecodeError = json.JSONDecodeError
except AttributeError:  # in Python 2.7
    t_JSONDecodeError = ValueError


class Session(collections.MutableMapping):
    """
    A simple dict-like class that is backed by a JSON file.

    All direct modifications will save the file. Indirect modifications should
    be followed by a call to `save_with_retry` or `save`.
    """

    def __init__(self, encoding=None):
        super(Session, self).__init__()
        self.filename = None
        self.data = {}
        self._encoding = encoding if encoding else 'utf-8-sig'

    def load(self, filename, max_age=0):
        self.filename = filename
        self.data = {}
        try:
            if max_age > 0:
                st = os.stat(self.filename)
                if st.st_mtime + max_age < time.time():
                    self.save()
            with codecs_open(self.filename, 'r', encoding=self._encoding) as f:
                self.data = json.load(f)
        except (OSError, IOError, t_JSONDecodeError) as load_exception:
            # OSError / IOError should imply file not found issues which are expected on fresh runs (e.g. on build
            # agents or new systems). A parse error indicates invalid/bad data in the file. We do not wish to warn
            # on missing files since we expect that, but do if the data isn't parsing as expected.
            log_level = logging.INFO
            if isinstance(load_exception, t_JSONDecodeError):
                log_level = logging.WARNING

            get_logger(__name__).log(log_level,
                                     "Failed to load or parse file %s. It will be overridden by default settings.",
                                     self.filename)
            self.save()

    def save(self):
        if self.filename:
            with codecs_open(self.filename, 'w', encoding=self._encoding) as f:
                json.dump(self.data, f)

    def save_with_retry(self, retries=5):
        for _ in range(retries - 1):
            try:
                self.save()
                break
            except OSError:
                time.sleep(0.1)
        else:
            self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data.setdefault(key, {})

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save_with_retry()

    def __delitem__(self, key):
        del self.data[key]
        self.save_with_retry()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


# ACCOUNT contains subscriptions information
ACCOUNT = Session()

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

# INDEX contains {top-level command: [command_modules and extensions]} mapping index
INDEX = Session()

# VERSIONS provides local versions and pypi versions.
# DO NOT USE it to get the current version of azure-cli,
# it could be lagged behind and can be used to check whether
# an upgrade of azure-cli happens
VERSIONS = Session()

# EXT_CMD_TREE provides command to extension name mapping
EXT_CMD_TREE = Session()

# CLOUD_ENDPOINTS provides endpoints/suffixes of clouds
CLOUD_ENDPOINTS = Session()
