#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import re
import sys


# http://noyobo.com/2015/11/13/ANSI-escape-code.html
# Reset all to default: 0
# Bold or increased intensity: 1
# Fraktur (Gothic): 20
# red: 31
# green: 32
# yellow: 33
# grey: 38
reset = "\x1b[0m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
green = "\x1b[32;20m"
yellow = "\x1b[33;20m"
grey = "\x1b[38;20m"
format = "%(message)s"
TITLE = sys.argv[1]
BODY = sys.argv[2]
words_to_check = {
            'Add': r'\b(added|adding|adds)\b',
            'Allow': r'\b(allowed|allowing|allows)\b',
            'Change': r'\b(changed|changing|changes)\b',
            'Deprecate': r'\b(deprecated|deprecating|deprecates)\b',
            'Disable': r'\b(disabled|disabling|disables)\b',
            'Enable': r'\b(enabled|enabling|enables)\b',
            'Fix': r'\b(fixed|fixing|fixes)\b',
            'Improve': r'\b(improved|improving|improves)\b',
            'Make': r'\b(made|making|makes)\b',
            'Move': r'\b(moved|moving|moves)\b',
            'Rename': r'\b(renamed|renaming|renames)\b',
            'Replace': r'\b(replaced|replacing|replaces)\b',
            'Remove': r'\b(removed|removing|removes)\b',
            'Support': r'\b(supported|supporting|supports)\b',
            'Update': r'\b(updated|updating|updates)\b',
            'Upgrade': r'\b(upgraded|upgrading|upgrades)\b',
        }


class CustomFormatter(logging.Formatter):
    # logging with color
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


def main():
    logger.info("Start check pull request ...\n")
    title = TITLE
    body = BODY.split('\r\n')
    sys.exit(1) if check_pull_request(title, body) else sys.exit(0)


def check_pull_request(title, body):
    if title.startswith('['):
        error_flag = regex_line(title)
        is_edit_history_note = False
        history_note_error_flag = False
        for line in body:
            if line.startswith('['):
                # get component name in []
                ref = re.findall(r'[\[](.*?)[\]]', line)
                if ref and ref[0] not in ['Component Name 1', 'Component Name 2']:
                    is_edit_history_note = True
                    history_note_error_flag = regex_line(line) or history_note_error_flag
		# If edit history notes, ignore title check result
        error_flag = error_flag if not is_edit_history_note else history_note_error_flag
    elif title.startswith('{'):
        error_flag = False
    else:
        logger.error('Pull Request title should start with [ or { , Please follow https://aka.ms/submitAzPR')
        error_flag = True
    return error_flag


def regex_line(line):
    error_flag = False
    enclosed_begin = False
    enclosed_end = True
    # Check Fix #number in title, just give a warning here, because it is not necessarily.
    if 'Fix' in line:
        sub_pattern = r'#\d'
        ref = re.findall(sub_pattern, line)
        if not ref:
            logger.warning('If it\'s related to fixing an issue, put Fix #number in title\n')
    for idx, i in enumerate(line):
        # ] } : must be followed by a space
        if i in [']', '}', ':']:
            try:
                assert line[idx + 1] == ' '
            except:
                logger.info('%s%s: missing space after %s', line, yellow, i)
                logger.error(' ' * idx + '↑')
                error_flag = True
        # az xxx commands must be enclosed in `, e.g., `az vm`
        if i == 'a' and line[idx + 1] == 'z' and line[idx + 2] == ' ':
            command = 'az '
            index = idx + 3
            while index < len(line) and line[index] != ':':
                command += line[index]
                index += 1
            try:
                assert line[idx - 1] == '`'
            except:
                logger.info('%s%s: missing ` around %s', line, yellow, command)
                logger.error(' ' * idx + '↑' + ' ' * (index - idx - 2) + '↑')
                error_flag = True
        if i == ':':
            # check extra space character before colon
            if idx - 1 >= 0 and line[idx - 1] == ' ':
                logger.info('%s%s: please delete extra space character before :', line, yellow)
                logger.error(' ' * (idx - 1) + '↑')
                error_flag = True
            # First word after the colon must be capitalized
            index = 0
            if line[idx + 1] == ' ' and line[idx + 2].islower() and line[idx + 2: idx + 5] != 'az ':
                index = idx + 2
            elif line[idx + 1] != ' ' and line[idx + 1].islower() and line[idx + 1: idx + 4] != 'az ':
                index = idx + 1
            if index:
                logger.info('%s%s: should use capital letters after :', line, yellow)
                logger.error(' ' * index + '↑')
                error_flag = True
        # --xxx parameters must be enclosed in `, e.g., `--size`
        if line[idx] == '`' and not enclosed_begin:
            enclosed_begin = True
            enclosed_end = False
        elif line[idx] == '`' and enclosed_begin:
            enclosed_begin = False
            enclosed_end = True
        if i == '-' and (idx + 1) < len(line) and line[idx + 1] == '-':
            if not enclosed_begin:
                param = '--'
                index = idx + 2
                while index < len(line) and line[index] not in [' ', '/']:
                    param += line[index]
                    index += 1
                try:
                    assert line[idx - 1] == '`'
                except:
                    logger.info('%s%s: missing ` around %s', line, yellow, param)
                    logger.error(' ' * idx + '↑' + ' ' * (index - idx - 2) + '↑')
                    error_flag = True
        # verb check: only check the first word after ] or :
        if i in [']', ':']:
            word = ''
            c = index = idx + 1 if line[idx + 1] != ' ' else idx + 2
            while index < len(line) and line[index] != ' ':
                word += line[index]
                index += 1
            for k, v in words_to_check.items():
                if re.findall(v, word, re.IGNORECASE):
                    logger.info(line)
                    logger.error(' ' * c + '↑')
                    logger.warning(
                        'Please use the right verb of%s %s %swith %s(%s)%s simple present tense in base form '
                        'and capitalized first letter to describe what is done, '
                        'follow https://aka.ms/submitAzPR\n', red, word, yellow, green, k, yellow)
                    error_flag = True
                    break
        # check extra consecutive spaces
        if i == ' ' and (idx + 1) < len(line) and line[idx + 1] == ' ':
            logger.info('%s%s: please delete the extra space character', line, yellow)
            logger.error(' ' * (idx + 1) + '↑')
            error_flag = True

    # last character check
    if line[-1] in ['.', ',', ' ']:
        logger.info('%s%s: please delete the last character', line, yellow)
        logger.error(' ' * idx + '↑')
        error_flag = True

    # check the ending ` character
    if not enclosed_end:
        logger.info('%s%s: unable to find the ending ` character', line, yellow)
        error_flag = True

    return error_flag


if __name__ == '__main__':
    main()
