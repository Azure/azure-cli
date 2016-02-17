import collections.abc
import json
import os
import time

from codecs import open

class Session(collections.abc.MutableMapping):
    '''A simple dict-like class that is backed by a JSON file.

    All direct modifications will save the file. Indirect modifications should
    be followed by a call to `save_with_retry` or `save`.
    '''

    def __init__(self):
        self.filename = None
        self.data = {}

    def load(self, filename, max_age=0):
        self.filename = filename
        self.data = {}
        try:
            if max_age > 0:
                st = os.stat(self.filename)
                if st.st_mtime + max_age < time.clock():
                    self.save()
            with open(self.filename, 'r', encoding='utf-8-sig') as f:
                self.data = json.load(f)
        except OSError:
            self.save()

    def save(self):
        if self.filename:
            with open(self.filename, 'w', encoding='utf-8-sig') as f:
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
