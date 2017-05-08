# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import unittest

import azclishell.frequency_heuristic as fh


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

    def test_heuristic(self):
        fh.update_frequency = _mock_update
        self.assertEqual(1, fh.frequency_measurement())

        fh.update_frequency = _mock_update2
        self.assertEqual(2, fh.frequency_measurement())

        fh.update_frequency = _mock_update3
        self.assertEqual(3, fh.frequency_measurement())


if __name__ == '__main__':
    unittest.main()
