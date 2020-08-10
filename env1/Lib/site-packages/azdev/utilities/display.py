# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import sys


def display(txt):
    """ Output to stderr """
    print(txt, file=sys.stderr)


def output(txt):
    """ Output to stdout """
    print(txt, file=sys.stdout)


def heading(txt):
    """ Create standard heading to stderr """
    line_len = len(txt) + 4
    display('\n' + '=' * line_len)
    display('| {} |'.format(txt))
    display('=' * line_len + '\n')


def subheading(txt):
    """ Create standard heading to stderr """
    line_len = len(txt) + 2
    display('\n {} '.format(txt))
    display('=' * line_len + '\n')
