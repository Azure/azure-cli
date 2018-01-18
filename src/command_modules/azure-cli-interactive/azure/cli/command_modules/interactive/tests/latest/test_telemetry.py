# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azclishell.telemetry import scrub


class TelemetryTest(unittest.TestCase):

    def test_scrubbing(self):
        # tests the scrubbing of parameters
        text1 = 'this is a --secret value wut wut'
        text2 = 'this has NO secret value'
        text3 = 'this is -my value -is alice --bob knows'
        text4 = 'this is -my value secrets secrets2 -is alice --bob knows'

        scrub_val = '*****'
        self.assertEqual(scrub(text1), 'this is a --secret {} {} {}'.format(
            scrub_val, scrub_val, scrub_val))
        self.assertEqual(scrub(text2), text2)
        self.assertEqual(scrub(text3), 'this is -my {} -is {} --bob {}'.format(
            scrub_val, scrub_val, scrub_val))
        self.assertEqual(scrub(text4), 'this is -my {} {} {} -is {} --bob {}'.format(
            scrub_val, scrub_val, scrub_val, scrub_val, scrub_val))


if __name__ == '__main__':
    unittest.main()
