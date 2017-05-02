# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

import azure.cli.core.commands.progress as progress


class MockOutstream(progress._ProgressViewBase):
    """ mock outstream for testing """
    def __init__(self, p_type=progress.ProgressType.Indeterminate):
        self.string = ''
        self.type = p_type

    def write(self, message):
        self.string = message

    def get_type(self):
        return self.type

    def flush(self):
        return self.string


class DetMockOutstream(progress._ProgressViewBase):
    """ mock outstream for testing """
    def __init__(self, p_type=progress.ProgressType.Determinate):
        self.string = ''
        self.type = p_type

    def write(self, message):
        self.string = message

    def get_type(self):
        return self.type

    def flush(self):
        return self.string


class TestProgress(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """ test the progress reporting """

    def test_det_model(self):
        """ test the determinate progress reporter """
        reporter = progress.DetProgressReporter()
        args = reporter.report()
        self.assertEqual(args['message'], '')
        self.assertEqual(args['percent'], 0)

        reporter.add({'message': 'Progress', 'total_val': 10, 'value': 0})
        self.assertEqual(reporter.message, 'Progress')
        self.assertEqual(reporter.curr_val, 0)
        self.assertEqual(reporter.total_val, 10)
        args = reporter.report()
        self.assertEqual(args['message'], 'Progress')
        self.assertEqual(args['percent'], 0)

        with self.assertRaises(AssertionError):
            reporter.add({'message': 'In words', 'total_val': -1, 'value': 10})
        with self.assertRaises(AssertionError):
            reporter.add({'message': 'In words', 'total_val': 1, 'value': -10})
        with self.assertRaises(AssertionError):
            reporter.add({'message': 'In words', 'total_val': 490, 'value': 10})

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
        self.assertEqual(view.get_type().value, progress.ProgressType.Indeterminate.value)
        before = view.spinner.total
        self.assertEqual(view.spinner.label, 'In Progress')
        view.write({})
        after = view.spinner.total
        self.assertTrue(after >= before)
        view.write(kwargs={'message': 'TESTING'})
        self.assertEqual(view.spinner.label, 'TESTING')

    def test_det_stdview(self):
        """ test the determinate progress standardout view """
        outstream = MockOutstream()
        view = progress.DeterminateStandardOut(out=outstream)
        self.assertEqual(view.get_type().value, progress.ProgressType.Determinate.value)
        view.write({'message': 'hihi', 'percent': .5})
        # 95 length, 48 complete, 4 dec percent
        bar_str = ('#' * 48).ljust(95)
        self.assertEqual(outstream.string, '\rhihi[{}]  50.0000%'.format(bar_str))

        view.write({'message': '', 'percent': .9})
        # 99 length, 90 complete, 4 dec percent
        bar_str = ('#' * 90).ljust(95)
        self.assertEqual(outstream.string, '\r[{}]  90.0000%'.format(bar_str))

    def test_controller(self):
        """ tests the controller for progress reporting """
        controller = progress.ProgressHook(progress.ProgressType.Indeterminate)
        view = MockOutstream()

        controller.init_progress(view)
        self.assertTrue(view in controller.active_progress)

        controller.begin()
        self.assertEqual(controller.active_progress[0].string['message'], 'Starting')

        controller.end()
        self.assertEqual(controller.active_progress[0].string['message'], 'Finished')

        controller = progress.ProgressHook(progress.ProgressType.Determinate)
        view = DetMockOutstream()

        controller.init_progress(view)
        self.assertTrue(view in controller.active_progress)

        start = controller.begin()
        self.assertTrue('Starting' in start)

        end = controller.end()
        self.assertTrue('Finished' in end)


if __name__ == '__main__':
    unittest.main()
