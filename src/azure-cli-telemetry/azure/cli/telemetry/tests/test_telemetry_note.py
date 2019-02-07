# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import tempfile
import shutil
import stat
import datetime
import time

import portalocker

from azure.cli.telemetry.components.telemetry_note import TelemetryNote


class TestTelemetryNote(unittest.TestCase):
    SAMPLE_TIME_1 = datetime.datetime(year=1999, month=12, day=31, hour=8, minute=12, second=13)
    SAMPLE_TIME_2 = datetime.datetime(year=2001, month=8, day=7, hour=21, minute=2, second=47)

    def setUp(self):
        self.workDir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workDir, ignore_errors=True)

    def test_create_telemetry_note_file_from_scratch(self):
        with TelemetryNote(self.workDir) as note:
            self.assert_modify_time(note.path, datetime.timedelta(seconds=1))
            self.assertTrue(os.path.exists(note.path))
            self.assertEqual(datetime.datetime.min, note.get_last_sent())

            with self.assertRaises(portalocker.AlreadyLocked):
                with TelemetryNote(self.workDir):
                    self.assertFalse(True)

            self.set_modify_time(note.path)

            note.touch()
            self.assert_modify_time(note.path, datetime.timedelta(seconds=1))

            note.update_telemetry_note(self.SAMPLE_TIME_1)

            # newly create file is not readable
            self.assertEqual(datetime.datetime.min, note.get_last_sent())

        with TelemetryNote(self.workDir) as note:
            self.assertEqual(self.SAMPLE_TIME_1, note.get_last_sent())

            with self.assertRaises(portalocker.AlreadyLocked):
                with TelemetryNote(self.workDir):
                    self.assertFalse(True)

    def test_open_telemetry_note_file(self):
        with open(TelemetryNote.get_file_path(self.workDir), mode='w') as fq:
            fq.write(self.SAMPLE_TIME_1.strftime('%Y-%m-%dT%H:%M:%S'))

        with TelemetryNote(self.workDir) as note:
            self.assertEqual(self.SAMPLE_TIME_1, note.get_last_sent())

            with self.assertRaises(portalocker.AlreadyLocked):
                with TelemetryNote(self.workDir):
                    self.assertFalse(True)

            note.update_telemetry_note(self.SAMPLE_TIME_2)

        with TelemetryNote(self.workDir) as note:
            self.assertEqual(self.SAMPLE_TIME_2, note.get_last_sent())

    def assert_modify_time(self, file_path, gap):
        modify_time = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
        self.assertTrue(datetime.datetime.now() - modify_time < gap)

    def set_modify_time(self, file_path, new_time=None):
        if not new_time:
            new_time = (datetime.datetime.now() - datetime.timedelta(minutes=5))

        expected_timestamp = time.mktime(new_time.timetuple()) + new_time.microsecond / 1E6
        os.utime(file_path, (expected_timestamp, expected_timestamp))

        modify_time = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
        actual_timestamp = time.mktime(modify_time.timetuple()) + modify_time.microsecond / 1E6
        self.assertAlmostEqual(expected_timestamp, actual_timestamp, delta=1E-6)


if __name__ == '__main__':
    unittest.main()
