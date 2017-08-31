# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
# pylint: disable=no-self-use,unused-argument

import os
import sys
import contextlib
import functools
import six

six.print_ = functools.partial(six.print_, flush=True)


# This is to prevent IoT SDK C output, but is not intrusive due to context
@contextlib.contextmanager
def block_stdout():
    devnull = open(os.devnull, 'w')
    orig_stdout_fno = os.dup(sys.stdout.fileno())
    os.dup2(devnull.fileno(), 1)
    try:
        yield
    finally:
        os.dup2(orig_stdout_fno, 1)


class Default_Msg_Callbacks(object):
    def open_complete_callback(self, context):
        return

    def send_complete_callback(self, context, messaging_result):
        return

    def feedback_received_callback(self, context, batch_user_id, batch_lock_token, feedback_records):
        six.print_('Batch userId                 : {0}'.format(batch_user_id))
        six.print_('Batch lockToken              : {0}'.format(batch_lock_token))
        if feedback_records:
            number_of_feedback_records = len(feedback_records)
            six.print_('Number of feedback records   : {0}'.format(
                number_of_feedback_records))

            for feedback_index in range(0, number_of_feedback_records):
                six.print_('Feedback record {0}'.format(feedback_index))
                six.print_('statusCode               : {0}'.format(
                    feedback_records[feedback_index]["statusCode"]))
                six.print_('description              : {0}'.format(
                    feedback_records[feedback_index]["description"]))
                six.print_('deviceId                 : {0}'.format(
                    feedback_records[feedback_index]["deviceId"]))
                six.print_('generationId             : {0}'.format(
                    feedback_records[feedback_index]["generationId"]))
                six.print_('correlationId            : {0}'.format(
                    feedback_records[feedback_index]["correlationId"]))
                six.print_('enqueuedTimeUtc          : {0}'.format(
                    feedback_records[feedback_index]["enqueuedTimeUtc"]))
                six.print_('originalMessageId        : {0}'.format(
                    feedback_records[feedback_index]["originalMessageId"]))
