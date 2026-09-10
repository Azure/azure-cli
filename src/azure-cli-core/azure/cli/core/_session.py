# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import json
import logging
import os
import stat
import tempfile
import time
from collections.abc import MutableMapping

from knack.log import get_logger


class Session(MutableMapping):
    """
    A simple dict-like class that is backed by a JSON file.

    All direct modifications will save the file. Indirect modifications should
    be followed by a call to `save_with_retry` or `save`.
    """

    def __init__(self, encoding=None):
        super().__init__()
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
            with open(self.filename, 'r', encoding=self._encoding) as f:
                self.data = json.load(f)
        except (OSError, json.JSONDecodeError) as load_exception:
            # OSError / IOError should imply file not found issues which are expected on fresh runs (e.g. on build
            # agents or new systems). A parse error indicates invalid/bad data in the file. We do not wish to warn
            # on missing files since we expect that, but do if the data isn't parsing as expected.
            log_level = logging.INFO
            if isinstance(load_exception, json.JSONDecodeError):
                log_level = logging.WARNING

            get_logger(__name__).log(log_level,
                                     "Failed to load or parse file %s. It will be overridden by default settings.",
                                     self.filename)
            self.save()

    def save(self):
        if not self.filename:
            return

        # Write to a temporary file in the same directory and rename it over the target, so the
        # file on disk is never observably incomplete. Opening the target with 'w' truncates it
        # in place, which leaves a window where a concurrent process reads zero or half a
        # document. That reader then fails to parse it and load() overwrites it with defaults,
        # so a process that only meant to read destroys the data.
        target = os.path.realpath(self.filename)
        directory = os.path.dirname(target) or os.curdir

        try:
            fd, temp_name = tempfile.mkstemp(dir=directory, prefix=os.path.basename(target) + '.',
                                             suffix='.tmp')
        except OSError as ex:
            if ex.errno not in (errno.EACCES, errno.EPERM, errno.EROFS):
                # Anything else, a full disk for instance, would also break the in place write and
                # would lose the file doing it, so let it surface instead.
                raise
            # The directory is not writable but the file is, which happens in locked down
            # containers and CI images. Writing in place still works there, so keep the old
            # behaviour rather than failing a save that used to succeed.
            with open(self.filename, 'w', encoding=self._encoding) as f:
                json.dump(self.data, f)
            return

        try:
            with os.fdopen(fd, 'w', encoding=self._encoding) as f:
                json.dump(self.data, f)
            # mkstemp creates the file 0o600. Carry over the permissions of the file being
            # replaced so a save does not silently tighten them.
            try:
                os.chmod(temp_name, stat.S_IMODE(os.stat(target).st_mode))
            except OSError:
                pass
            os.replace(temp_name, target)
        except BaseException:
            # BaseException so that an interrupt does not leave the temporary file behind.
            try:
                os.remove(temp_name)
            except OSError:
                pass
            raise

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

# EXTENSION_INDEX contains top-level command mappings for installed extensions
EXTENSION_INDEX = Session()

# HELP_INDEX contains cached help summaries for top-level help display
HELP_INDEX = Session()

# EXTENSION_HELP_INDEX contains extension-only help overlay for top-level help display
EXTENSION_HELP_INDEX = Session()

# VERSIONS provides local versions and pypi versions.
# DO NOT USE it to get the current version of azure-cli,
# it could be lagged behind and can be used to check whether
# an upgrade of azure-cli happens
VERSIONS = Session()

# EXT_CMD_TREE provides command to extension name mapping
EXT_CMD_TREE = Session()

# CLOUD_ENDPOINTS provides endpoints/suffixes of clouds
CLOUD_ENDPOINTS = Session()
