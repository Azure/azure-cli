# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

import azure.cli.core.commands.progress as progress


class MockOutstream(progress.ProgressViewBase):
    def __init__(self):
        self.string = ''

    def write(self, message):
        self.string = message

    def flush(self):
        pass


class TestProgress(unittest.TestCase):
    def test_progress_indicator_det_model(self):
        # test the progress reporter
        reporter = progress.ProgressReporter()
        args = reporter.report()
        self.assertEqual(args['message'], '')
        self.assertEqual(args['percent'], None)

        reporter.add(message='Progress', total_val=10, value=0)
        self.assertEqual(reporter.message, 'Progress')
        self.assertEqual(reporter.value, 0)
        self.assertEqual(reporter.total_val, 10)
        args = reporter.report()
        self.assertEqual(args['message'], 'Progress')
        self.assertEqual(args['percent'], 0)

        with self.assertRaises(AssertionError):
            reporter.add(message='In words', total_val=-1, value=10)
        with self.assertRaises(AssertionError):
            reporter.add(message='In words', total_val=1, value=-10)
        with self.assertRaises(AssertionError):
            reporter.add(message='In words', total_val=30, value=12340)

        reporter = progress.ProgressReporter()
        message = reporter.report()
        self.assertEqual(message['message'], '')

        reporter.add(message='Progress')
        self.assertEqual(reporter.message, 'Progress')

        message = reporter.report()
        self.assertEqual(message['message'], 'Progress')

    def test_progress_indicator_indet_stdview(self):
        # tests the indeterminate progress standardout view
        outstream = MockOutstream()
        view = progress.IndeterminateStandardOut(out=outstream)
        view.write({})
        self.assertEqual(view.spinner.label, 'In Progress')
        before = view.spinner.total
        view.write({})
        after = view.spinner.total
        self.assertTrue(after == before)
        view.write({'message': 'TESTING'})

    def test_progress_indicator_det_stdview(self):
        # test the determinate progress standardout view
        outstream = MockOutstream()
        view = progress.DeterminateStandardOut(out=outstream)
        view.write({'message': 'hihi', 'percent': .5})
        # 95 length, 48 complete, 4 dec percent
        bar_str = ('#' * int(.5 * 65)).ljust(65)
        self.assertEqual(outstream.string, '\rhihi[{}]  {:.4%}'.format(bar_str, .5))

        view.write({'message': '', 'percent': .9})
        # 99 length, 90 complete, 4 dec percent
        bar_str = ('#' * int(.9 * 69)).ljust(69)
        self.assertEqual(outstream.string, '\r[{}]  {:.4%}'.format(bar_str, .9))

    def test_progress_indicator_controller(self):
        # tests the controller for progress reporting
        controller = progress.ProgressHook()
        view = MockOutstream()

        controller.init_progress(view)
        self.assertTrue(view == controller.active_progress)

        controller.begin()

        self.assertEqual(controller.active_progress.string['message'], 'Starting')

        controller.end()
        self.assertEqual(controller.active_progress.string['message'], 'Finished')


if __name__ == '__main__':
    unittest.main()
