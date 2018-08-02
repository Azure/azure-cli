# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import datetime

import portalocker.utils


class TelemetryNote(portalocker.utils.Lock):
    def __init__(self, config_dir):
        from azure.cli.telemetry.components.telemetry_logging import get_logger

        self._path = self.get_file_path(config_dir)
        self._logger = get_logger('note')

        if not os.path.exists(self._path):
            super(TelemetryNote, self).__init__(self._path, mode='w', timeout=0.1, fail_when_locked=True)
        else:
            super(TelemetryNote, self).__init__(self._path, mode='r+', timeout=1, fail_when_locked=True)

    @staticmethod
    def get_file_path(config_dir):
        from azure.cli.telemetry.const import TELEMETRY_NOTE_NAME
        return os.path.join(config_dir, TELEMETRY_NOTE_NAME)

    @property
    def path(self):
        return self._path

    def get_last_sent(self):
        """ Read the timestamp of the last sent telemetry record from the telemetry note file. """
        raw = 'N/A'
        fallback = datetime.datetime.min

        try:
            raw = self.fh.read().strip()
            last_send = datetime.datetime.strptime(raw, '%Y-%m-%dT%H:%M:%S')
            self._logger.info("Read timestamp from the note. The last send was %s.", last_send)
            return last_send
        except (AttributeError, ValueError, IOError) as err:
            self._logger.warning("Fail to parse or read the timestamp '%s' in the note file. Set the last send time "
                                 "to minimal. Reason: %s", raw, err)
            return fallback

    def update_telemetry_note(self, next_send):
        # note update retry
        for retry in range(3):
            try:
                self.fh.seek(0)
                self.fh.write(next_send.strftime('%Y-%m-%dT%H:%M:%S'))
                self.fh.truncate()
                break
            except IOError:
                self._logger.warning('Fail to update the note file. This is the %d try.', retry + 1)
        else:
            # TODO: how to save this?
            self._logger.error('Fail to update the note file after three retry.')

        self._logger.info('Update the last send in note to %s', next_send)
        self.touch()

    def touch(self):
        st_atime = os.stat(self.path).st_atime
        st_mtime = time.time()
        os.utime(self.path, (st_atime, st_mtime))
        self._logger.info('Update the note mtime to %s', datetime.datetime.fromtimestamp(st_mtime))

    def __enter__(self):
        self._logger.debug('acquiring lock')
        self.acquire()
        self._logger.debug('acquired lock')
        return self
