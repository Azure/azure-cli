# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
import sys
import argparse
from datetime import datetime

from ..utilities.path import get_all_module_paths

HISTORY_FILENAME = 'HISTORY.rst'

IGNORE_LINES = ['.. :changelog:', 'Release History']
UNRELEASED = 'unreleased'


def _parse_date_on_line(line):
    try:
        # Line ends in format '(YYYY-MM-DD)' (ignoring ending whitespace if any)
        return _parse_date(line.strip()[-11:-1])
    except (ValueError, TypeError):
        return None


def get_note_content(history, date_after):
    note_content_lines = []
    found_first_release = False
    with open(history) as f:
        lines = f.read().splitlines()
        for line in lines:
            if not line or line in IGNORE_LINES or all([char == line[0] for char in line]):
                # line empty OR line in ignore list OR line all the same char (likely a heading)
                continue
            line_date = _parse_date_on_line(line)
            if line_date:
                found_first_release = True
            if line_date and line_date <= date_after:
                # Reached the date specified so don't continue
                break
            if line_date:
                # Don't include the date lines in the release notes
                continue
            if not found_first_release:
                # use this to ignore any unreleased notes
                continue
            # okay to add the line
            note_content_lines.append(line)
    return '\n'.join(note_content_lines)


def generate_release_notes(date_after):
    notes = []
    for comp_name, comp_path in get_all_module_paths():
        history_path = os.path.join(comp_path, HISTORY_FILENAME)
        if os.path.exists(history_path):
            note_content = get_note_content(history_path, date_after)
            if note_content:
                # Only add note if there where actually changes.
                notes.append({'title': comp_name.upper(), 'content': note_content})
    return notes


def _parse_date(value):
    yyyy, mm, dd = value.split('-')
    return datetime(int(yyyy), int(mm), int(dd))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate release notes for all components. "
                    "Example 'python -m scripts.automation.release.notes -d 2017-04-03 > release_notes.txt'")
    parser.add_argument('--date', '-d',
                        help='The date after which to collate release notes for (format is YYYY-MM-DD)',
                        required=True, type=_parse_date)
    args = parser.parse_args()
    all_notes = generate_release_notes(args.date)
    for n in all_notes:
        print(n['title'])
        print('-'*len(n['title']))
        print(n['content'])
        print()

