# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import MutableMapping
import json
import os

from azure.cli.core.decorators import retry
from knack.log import get_logger

logger = get_logger(__name__)


class BinaryCache(MutableMapping):
    """
    Derived from azure.cli.core._session.Session.
    A simple dict-like class that is backed by a JSON file.

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
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # The cache file has not been created. This is expected. No need to retry.
            logger.debug("%s not found. Using a fresh one.", self.filename)
            return {}

    def load(self):
        logger.debug("load: %s", self.filename)
        try:
            self.data = self._load()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # If we still get exception after retry, ignore all types of exceptions and use a new cache.
            # - json.JSONDecodeError is caused by corrupted or legacy pickle cache file.
            # - ValueError/KeyError from malformed JSON content.
            logger.debug("Failed to load cache: %s. Using a fresh one.", ex)
            self.data = {}  # Ignore a non-existing or corrupted http_cache

    @retry()
    def _save(self):
        fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)

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
