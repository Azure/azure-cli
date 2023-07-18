# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys


def display(txt):
    """ Output to stderr """
    print(txt, file=sys.stderr)


def output(txt):
    """ Output to stdout """
    print(txt, file=sys.stdout)


def get_print_format(records):
    """Find the best format to display the given list of records in table format"""
    if not records:
        raise ValueError('missing parameter records')

    if not isinstance(records, list):
        raise ValueError('records is not a list')

    size = len(records[0])
    max_len = [0] * size

    col_index = list(range(size))
    for rec in records:
        if len(rec) != size:
            raise ValueError('size of elements in the records set are not equal')

        for i in col_index:
            max_len[i] = max(max_len[i], len(str(rec[i])))

    recommend_format = ''
    for each in max_len:
        recommend_format += '{:' + str(each + 2) + '}'

    return recommend_format, max_len


def print_records(records, print_format=None, title=None, foot_notes=None):
    """Print a list of tuples with a print format."""
    print_format = print_format or get_print_format(records)[0]
    if print_format is None:
        raise ValueError('print format is required')

    print()
    print("Summary" + ': {}'.format(title) if title is not None else '')
    print("==========================")
    for rec in records:
        print(print_format.format(*rec))
    print("==========================")
    if foot_notes:
        for each in foot_notes:
            print('* ' + each)


def print_heading(heading, f=None):
    lines = heading.splitlines()
    header_len = max(len(l) for l in lines)
    print('{0}\n{1}\n{0}'.format('=' * header_len, heading), file=f)
