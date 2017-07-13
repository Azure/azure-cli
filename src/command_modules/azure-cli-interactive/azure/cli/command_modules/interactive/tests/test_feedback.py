# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import unittest
import tempfile

import azclishell.frequency_heuristic as fh
from azclishell.configuration import CONFIGURATION, get_config_dir as shell_config

SHELL_CONFIG = CONFIGURATION


def _mock_update():
    return {fh.day_format(datetime.datetime.utcnow()): 1}


def _mock_update2():
    return {
        fh.day_format(datetime.datetime.utcnow()): 2,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=2)): 1}


def _mock_update3():
    return {
        fh.day_format(datetime.datetime.utcnow()): 19,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=18)): 5,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=27)): 2,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=28)): 2,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=100)): 1,
        fh.day_format(datetime.datetime.utcnow() - datetime.timedelta(days=200)): 1}


class FeedbackTest(unittest.TestCase):
    """ tests the frequncy heuristic """
    def __init__(self, *args, **kwargs):
        super(FeedbackTest, self).__init__(*args, **kwargs)
        self.norm_update = fh.update_frequency

    def test_heuristic(self):
        # test the correct logging of time for frequency
        fh.update_frequency = _mock_update
        self.assertEqual(1, fh.frequency_measurement())

        fh.update_frequency = _mock_update2
        self.assertEqual(2, fh.frequency_measurement())

        fh.update_frequency = _mock_update3
        self.assertEqual(3, fh.frequency_measurement())

    def test_update_freq(self):
        # tests updating the files for frequency
        fh.update_frequency = self.norm_update
        now = fh.day_format(datetime.datetime.now())

        _, fh.FREQUENCY_PATH = tempfile.mkstemp()

        # with a file
        json_freq = fh.update_frequency()
        self.assertEqual(json_freq, {now: 1})
        json_freq = fh.update_frequency()
        self.assertEqual(json_freq, {now: 2})

    def test_update_freq_no_file(self):
        # tests updating the files for frequency with no file written
        fh.update_frequency = self.norm_update

        _, fh.FREQUENCY_PATH = tempfile.mkstemp()

        if os.path.exists(fh.FREQUENCY_PATH):
            os.remove(fh.FREQUENCY_PATH)

        # without a file already written
        json_freq = fh.update_frequency()
        now = fh.day_format(datetime.datetime.now())
        self.assertEqual(json_freq, {now: 1})

        if os.path.exists(fh.FREQUENCY_PATH):
            os.remove(fh.FREQUENCY_PATH)


if __name__ == '__main__':
    unittest.main()
