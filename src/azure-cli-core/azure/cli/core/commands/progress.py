# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys

from humanfriendly.terminal.spinners import Spinner

BAR_LEN = 70
EMPTY_LINE = ' ' * BAR_LEN


class ProgressViewBase:
    """ a view base for progress reporting """
    def __init__(self, out):
        self.out = out

    def write(self, args):
        """ writes the progress """
        raise NotImplementedError

    def flush(self):
        """ flushes the message out the pipeline"""
        raise NotImplementedError

    def clear(self):
        """ resets the view to neutral """
        pass  # pylint: disable=unnecessary-pass


class ProgressReporter:
    """ generic progress reporter """
    def __init__(self, message='', value=None, total_value=None):
        self.message = message
        self.value = value
        self.total_val = total_value
        self.closed = False

    def add(self, **kwargs):
        """
        adds a progress report
        :param kwargs: dictionary containing 'message', 'total_val', 'value'
        """
        message = kwargs.get('message', self.message)
        total_val = kwargs.get('total_val', self.total_val)
        value = kwargs.get('value', self.value)
        if value and total_val:
            assert 0 <= value <= total_val
            self.closed = value == total_val
        self.total_val = total_val
        self.value = value
        self.message = message

    def report(self):
        """ report the progress """
        percent = self.value / self.total_val if self.value is not None and self.total_val else None
        return {'message': self.message, 'percent': percent}


class ProgressHook:
    """ sends the progress to the view """
    def __init__(self):
        self.reporter = ProgressReporter()
        self.active_progress = None

    def init_progress(self, progress_view):
        """ activate a view """
        self.active_progress = progress_view

    def add(self, **kwargs):
        """ adds a progress report """
        self.reporter.add(**kwargs)
        self.update()

    def update(self):
        """ updates the view with the progress """
        self.active_progress.write(self.reporter.report())
        self.active_progress.flush()

    def stop(self):
        """ if there is an abupt stop before ending """
        self.reporter.closed = True
        self.add(message='Interrupted')
        self.active_progress.clear()

    def begin(self, **kwargs):
        """ start reporting progress """
        kwargs['message'] = kwargs.get('message', 'Starting')
        self.add(**kwargs)
        self.reporter.closed = False

    def end(self, **kwargs):
        """ ending reporting of progress """
        kwargs['message'] = kwargs.get('message', 'Finished')
        self.reporter.closed = True
        self.add(**kwargs)
        self.active_progress.clear()

    def is_running(self):
        """ whether progress is continuing """
        return not self.reporter.closed


class IndeterminateStandardOut(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self, out=None, spinner=None):
        super().__init__(
            out if out else sys.stderr)
        self.spinner = spinner

    def write(self, args):
        """
        writes the progress
        :param args: dictionary containing key 'message'
        """
        if self.spinner is None:
            self.spinner = Spinner(  # pylint: disable=no-member
                label='In Progress', stream=self.out, hide_cursor=False)
        msg = args.get('message', 'In Progress')
        try:
            self.spinner.step(label=msg)
        except OSError:
            pass

    def clear(self):
        self.spinner.clear()
        self.out.flush()

    def flush(self):
        self.out.flush()


def _format_value(msg, percent):
    bar_len = BAR_LEN - len(msg) - 1
    completed = int(bar_len * percent)

    message = '\r{}['.format(msg)
    message += ('#' * completed).ljust(bar_len)
    message += ']  {:.4%}'.format(percent)
    return message


class DeterminateStandardOut(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super().__init__(out if out else sys.stderr)

    def write(self, args):
        """
        writes the progress
        :param args: args is a dictionary containing 'percent', 'message'
        """
        percent = args.get('percent', 0)
        message = args.get('message', '')

        if percent:
            progress = _format_value(message, percent)
            self.out.write(progress)

    def clear(self):
        self.out.write('\n')

    def flush(self):
        self.out.flush()


def get_progress_view(determinant=False, outstream=sys.stderr, spinner=None):
    """ gets your view """
    if determinant:
        return DeterminateStandardOut(out=outstream)
    return IndeterminateStandardOut(out=outstream, spinner=spinner)


class IndeterminateProgressBar:
    """ Define progress bar update view """
    def __init__(self, cli_ctx, message="Running"):
        self.cli_ctx = cli_ctx
        self.message = message
        self.hook = self.cli_ctx.get_progress_controller(
            det=False,
            spinner=Spinner(  # pylint: disable=no-member
                label='Running',
                stream=sys.stderr,
                hide_cursor=False))

    def begin(self):
        self.hook.begin()

    def stop(self):
        self.hook.stop()

    def update_progress(self):
        self.hook.add(message=self.message)

    def update_progress_with_msg(self, message):
        if message != "":
            self.hook.add(message=message)
        else:
            self.hook.add(message=self.message)

    def end(self):
        self.hook.end()
