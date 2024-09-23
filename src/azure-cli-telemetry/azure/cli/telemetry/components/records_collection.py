# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import stat


class RecordsCollection:
    def __init__(self, cache_dir):
        from azure.cli.telemetry.components.telemetry_logging import get_logger

        self._records = []
        self._logger = get_logger('records')
        self._cache_dir = cache_dir

    def __iter__(self):
        return self._records.__iter__()

    def snapshot_and_read(self):
        """ Scan the telemetry cache files. """
        if not os.path.isdir(self._cache_dir):
            return

        # Collect all cache/cache.x files
        candidates = [(fn, os.stat(os.path.join(self._cache_dir, fn))) for fn in os.listdir(self._cache_dir)]

        # sort the cache files base on their last modification time.
        candidates = [(fn, file_stat) for fn, file_stat in candidates if stat.S_ISREG(file_stat.st_mode)]
        candidates.sort(key=lambda pair: pair[1].st_mtime, reverse=True)  # move the newer cache file first

        if not candidates:
            self._logger.info('No cache to be uploaded.')
            return

        self._logger.info('%d cache files to upload.', len(candidates))

        for each in os.listdir(self._cache_dir):
            self._read_file(os.path.join(self._cache_dir, each))

        shutil.rmtree(self._cache_dir,
                      ignore_errors=True,
                      onerror=lambda _, p, tr: self._logger.error('Fail to remove file %s', p))
        self._logger.info('Remove directory %s', self._cache_dir)

    def _read_file(self, path):
        """ Read content of a telemetry cache file and parse them into records. """
        try:
            with open(path, mode='r') as fh:
                for line in fh.readlines():
                    self._add_record(line)

                self._logger.info("Processed file %s into %d records.", path, len(self._records))
        except IOError as err:
            self._logger.warning("Fail to open file %s. Reason: %s.", path, err)

    def _add_record(self, content_line):
        """ Parse a line in the recording file. """
        try:
            _, content = content_line.split(',', 1)
            self._records.append(content)
        except ValueError as err:
            self._logger.warning("Fail to parse a line of the record %s. Error %s.", content_line, err)
