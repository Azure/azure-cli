# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

import azure.cli.core.commands.progress as progress

# @mock.patch('azure.cli.core.progress', ...)

class TestProgress(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """ test the progress reporting """

    def test_det_model(self):
        """ test the determinate progress reporter """
        reporter = progress.DetProgressReporter()
        message, percent = reporter.report()
        self.assertEqual(message, '')
        self.assertEqual(percent, None)

        reporter.add('Progress', 0, 10)
        self.assertEqual(reporter.message, 'Progress')
        self.assertEqual(reporter.curr_val, 0)
        self.assertEqual(reporter.total_val, 10)
        message, percent = reporter.report()
        self.assertEqual(message, 'Progress')
        self.assertEqual(percent, 0.0)

        with self.assertRaises(AssertionError):
            reporter.add('In words', -1, 10)
        with self.assertRaises(AssertionError):
            reporter.add('In words', 1, -10)
        with self.assertRaises(AssertionError):
            reporter.add('In words', 490, 10)

    def test_indet_model(self):
        """ test the indetermiante progress reporter """
        reporter = progress.InDetProgressReporter()
        message = reporter.report()
        self.assertEqual(message, '')

        reporter.add('Progress')
        self.assertEqual(reporter.message, 'Progress')

        message = reporter.report()
        self.assertEqual(message, 'Progress')

    def test_indet_stdview(self):
        """ tests the indeterminate progress standardout view """
        view = progress.IndeterminateStandardOut()
        self.assertEqual(view.get_type, progress.ProgressType.Indeterminate)
        before = view.spinner.total
        self.assertEqual(view.spinner.label, 'In Progress')
        view.write({})
        after = view.spinner.total
        self.assertTrue(after > before)
        view.write({'message':'TESTING'})
        self.assertEqual(view.spinner.label, 'TESTING')

    def test_det_stdview(self):
        """ test the determinate progress standardout view """
        view = progress.DeterminateStandardOut()
        self.assertEqual(view.get_type, progress.ProgressType.Determinate)



if __name__ == '__main__':
    unittest.main()
