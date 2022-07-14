# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import os
import shutil
import stat
import tempfile
from knack.config import CLIConfig


class RecordsCollection:
    def __init__(self, last_sent, config_dir):
        from azure.cli.telemetry.components.telemetry_logging import get_logger

        self._last_sent = last_sent
        self._next_send = last_sent
        self._records = []
        self._logger = get_logger('records')
        self._config_dir = config_dir

    def __iter__(self):
        return self._records.__iter__()

    @property
    def next_send(self):
        return self._next_send

    # pylint: disable=line-too-long
    def snapshot_and_read(self):
        """ Scan the telemetry cache files and move all the rotated files to a temp directory. """
        from azure.cli.telemetry.const import TELEMETRY_CACHE_DIR

        folder = os.path.join(self._config_dir, TELEMETRY_CACHE_DIR)
        if not os.path.isdir(folder):
            return

        # Collect all cache.x files. If it has been a long time since last sent, also collect cache file itself.
        include_cache = datetime.datetime.now() - self._last_sent > datetime.timedelta(hours=self._get_threshold_config())
        candidates = [(fn, os.stat(os.path.join(folder, fn))) for fn in os.listdir(folder) if include_cache or fn != 'cache']

        # sort the cache files base on their last modification time.
        candidates = [(fn, file_stat) for fn, file_stat in candidates if stat.S_ISREG(file_stat.st_mode)]
        candidates.sort(key=lambda pair: pair[1].st_mtime, reverse=True)  # move the newer cache file first

        if not candidates:
            self._logger.info('No cache to be uploaded.')
            return

        tmp = tempfile.mkdtemp()
        self._logger.info('%d cache files to move.', len(candidates))
        self._logger.info('Create temp folder %s', tmp)

        for each in candidates:
            if stat.S_ISREG(each[1].st_mode):
                try:
                    # Platform question: if this op is atom
                    shutil.move(os.path.join(folder, each[0]), os.path.join(tmp, each[0]))
                    self._logger.info('Move file %s to %s', os.path.join(folder, each[0]), os.path.join(tmp, each[0]))
                except IOError as err:
                    self._logger.warning('Fail to move file from %s to %s. Reason: %s.',
                                         os.path.join(folder, each[0]), os.path.join(tmp, each[0]), err)

        for each in os.listdir(tmp):
            self._read_file(os.path.join(tmp, each))

        shutil.rmtree(tmp,
                      ignore_errors=True,
                      onerror=lambda _, p, tr: self._logger.error('Fail to remove file %s', p))
        self._logger.info('Remove directory %s', tmp)

    def _get_threshold_config(self):
        config = CLIConfig(config_dir=self._config_dir)
        threshold = config.getint('telemetry', 'push_data_threshold', fallback=24)
        # the threshold for push telemetry can't be less than 1 hour, default value is 24 hours
        return threshold if threshold >= 1 else 24

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
            time, content = content_line.split(',', 1)
            time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
            if time > self._last_sent:
                self._next_send = max(self._next_send, time)
                self._records.append(content)
        except ValueError as err:
            self._logger.warning("Fail to parse a line of the record %s. Error %s.", content_line, err)
