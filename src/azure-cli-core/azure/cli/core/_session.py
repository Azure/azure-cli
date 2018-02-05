# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
try:
    import collections.abc as collections
except ImportError:
    import collections


from codecs import open as codecs_open


class Session(collections.MutableMapping):
    '''A simple dict-like class that is backed by a JSON file.

    All direct modifications will save the file. Indirect modifications should
    be followed by a call to `save_with_retry` or `save`.
    '''

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
                if st.st_mtime + max_age < time.clock():
                    self.save()
            with codecs_open(self.filename, 'r', encoding=self._encoding) as f:
                self.data = json.load(f)
        except (OSError, IOError):
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
