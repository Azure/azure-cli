# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import json
import logging
import os
import time
try:
    import collections.abc as collections
except ImportError:
    import collections


logger = logging.getLogger(__name__)


class FileCache(collections.MutableMapping):
    """A simple dict-like class that is backed by a JSON file.

    All direct modifications will save the file. Indirect modifications should
    be followed by a call to `save_with_retry` or `save`.
    """

    def __init__(self, file_name, max_age=0):
        super(FileCache, self).__init__()
        self.file_name = file_name
        self.max_age = max_age
        self.data = {}
        self.initial_load_occurred = False

    def load(self):
        self.data = {}
        try:
            if os.path.isfile(self.file_name):
                if self.max_age > 0 and os.stat(self.file_name).st_mtime + self.max_age < time.time():
                    logger.debug('Cache file expired: %s', file=self.file_name)
                    os.remove(self.file_name)
                else:
                    logger.debug('Loading cache file: %s', self.file_name)
                    self.data = get_file_json(self.file_name, throw_on_empty=False) or {}
            else:
                logger.debug('Cache file does not exist: %s', self.file_name)
        except Exception as ex:
            logger.debug(ex, exc_info=True)
            # file is missing or corrupt so attempt to delete it
            try:
                os.remove(self.file_name)
            except Exception as ex2:
                logger.debug(ex2, exc_info=True)
        self.initial_load_occurred = True

    def save(self):
        self._check_for_initial_load()
        self._save()

    def _save(self):
        if self.file_name:
            with os.fdopen(os.open(self.file_name, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600), 'w+') as cred_file:
                cred_file.write(json.dumps(self.data))

    def save_with_retry(self, retries=5):
        self._check_for_initial_load()
        for _ in range(retries - 1):
            try:
                self.save()
                break
            except OSError:
                time.sleep(0.1)
        else:
            self.save()

    def clear(self):
        if os.path.isfile(self.file_name):
            logger.info("Deleting file: " + self.file_name)
            os.remove(self.file_name)
        else:
            logger.info("File does not exist: " + self.file_name)

    def get(self, key, default=None):
        self._check_for_initial_load()
        return self.data.get(key, default)

    def __getitem__(self, key):
        self._check_for_initial_load()
        return self.data.setdefault(key, {})

    def __setitem__(self, key, value):
        self._check_for_initial_load()
        self.data[key] = value
        self.save_with_retry()

    def __delitem__(self, key):
        self._check_for_initial_load()
        del self.data[key]
        self.save_with_retry()

    def __iter__(self):
        self._check_for_initial_load()
        return iter(self.data)

    def __len__(self):
        self._check_for_initial_load()
        return len(self.data)

    def _check_for_initial_load(self):
        if not self.initial_load_occurred:
            self.load()


def get_cache_dir():
    vsts_cache_dir = os.getenv('VSTS_CACHE_DIR', None) or os.path.expanduser(os.path.join('~', '.vsts', 'python-sdk',
                                                                                          'cache'))
    if not os.path.exists(vsts_cache_dir):
        os.makedirs(vsts_cache_dir)
    return vsts_cache_dir


DEFAULT_MAX_AGE = 3600 * 12  # 12 hours
DEFAULT_CACHE_DIR = get_cache_dir()


def get_cache(name, max_age=DEFAULT_MAX_AGE, cache_dir=DEFAULT_CACHE_DIR):
    file_name = os.path.join(cache_dir, name + '.json')
    return FileCache(file_name, max_age)


OPTIONS_CACHE = get_cache('options')
RESOURCE_CACHE = get_cache('resources')


# Code below this point from azure-cli-core
# https://github.com/Azure/azure-cli/blob/master/src/azure-cli-core/azure/cli/core/util.py

def get_file_json(file_path, throw_on_empty=True, preserve_order=False):
    content = read_file_content(file_path)
    if not content and not throw_on_empty:
        return None
    return shell_safe_json_parse(content, preserve_order)


def read_file_content(file_path, allow_binary=False):
    from codecs import open as codecs_open
    # Note, always put 'utf-8-sig' first, so that BOM in WinOS won't cause trouble.
    for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be']:
        try:
            with codecs_open(file_path, encoding=encoding) as f:
                logger.debug("attempting to read file %s as %s", file_path, encoding)
                return f.read()
        except UnicodeDecodeError:
            if allow_binary:
                with open(file_path, 'rb') as input_file:
                    logger.debug("attempting to read file %s as binary", file_path)
                    return base64.b64encode(input_file.read()).decode("utf-8")
            else:
                raise
        except UnicodeError:
            pass

    raise ValueError('Failed to decode file {} - unknown decoding'.format(file_path))


def shell_safe_json_parse(json_or_dict_string, preserve_order=False):
    """ Allows the passing of JSON or Python dictionary strings. This is needed because certain
    JSON strings in CMD shell are not received in main's argv. This allows the user to specify
    the alternative notation, which does not have this problem (but is technically not JSON). """
    try:
        if not preserve_order:
            return json.loads(json_or_dict_string)
        from collections import OrderedDict
        return json.loads(json_or_dict_string, object_pairs_hook=OrderedDict)
    except ValueError:
        import ast
        return ast.literal_eval(json_or_dict_string)
