# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections.abc as collections
import pickle

from azure.cli.core.decorators import retry
from knack.log import get_logger

logger = get_logger(__name__)


class BinaryCache(collections.MutableMapping):
    """
    Derived from azure.cli.core._session.Session.
    A simple dict-like class that is backed by a binary file.

    All direct modifications with `__setitem__` and `__delitem__` will save the file.
    Indirect modifications should be followed by a call to `save`.
    """

    def __init__(self, file_name):
        super().__init__()
        self.filename = file_name
        self.data = {}
        self.load()

    @retry()
    def _load(self):
        """Load cache with retry. If it still fails at last, raise the original exception as-is."""
        try:
            with open(self.filename, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            # The cache file has not been created. This is expected. No need to retry.
            logger.debug("%s not found. Using a fresh one.", self.filename)
            return {}

    def load(self):
        logger.debug("load: %s", self.filename)
        try:
            self.data = self._load()
        except (pickle.UnpicklingError, EOFError) as ex:
            # We still get exception after retry:
            # - pickle.UnpicklingError is caused by corrupted cache file, perhaps due to concurrent writes.
            # - EOFError is caused by empty cache file created by other az instance, but hasn't been filled yet.
            logger.debug("Failed to load cache: %s. Using a fresh one.", ex)
            self.data = {}  # Ignore a non-existing or corrupted http_cache

    @retry()
    def _save(self):
        with open(self.filename, 'wb') as f:
            # At this point, an empty cache file will be created. Loading this cache file will
            # raise EOFError. This can be simulated by adding time.sleep(30) here.
            # So during loading, EOFError is ignored.
            pickle.dump(self.data, f)

    def save(self):
        logger.debug("save: %s", self.filename)
        # If 2 processes write at the same time, the cache will be corrupted,
        # but that is fine. Subsequent runs would reach eventual consistency.
        self._save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

    def __delitem__(self, key):
        del self.data[key]
        self.save()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
