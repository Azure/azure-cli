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
# yellow: 33
# grey: 38
reset = "\x1b[0m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
yellow = "\x1b[33;20m"
grey = "\x1b[38;20m"
format = "%(message)s"
TITLE = sys.argv[1]
BODY = sys.argv[2]


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
        for line in body:
            if line.startswith('['):
                error_flag = regex_line(line) or error_flag
    elif title.startswith('{'):
        error_flag = False
    else:
        logger.error('Pull Request title should start with [ or { , Please follow https://aka.ms/submitAzPR')
        error_flag = True
    return error_flag


def regex_line(line):
    error_flag = False
    # Check each line for these words, case insensitive
    sub_pattern = r'\b(added|adding|adds|changed|changing|changes|deprecated|deprecating|deprecates|fixed|fixing|fixes|made|making|makes|removed|removing|removes|updated|updating|updates)\b'
    ref = re.findall(sub_pattern, line, re.IGNORECASE)
    if ref:
        logger.warning('Please use the right verb of%s %s %swith simple present tense in base form and capitalized first letter to describe what is done, '
                       'follow https://aka.ms/submitAzPR\n', red, ref, yellow)
        error_flag = True
    # Check Fix #number in title, just give a warning here, because it is not necessarily
    if 'Fix' in line:
        sub_pattern = r'#\d'
        ref = re.findall(sub_pattern, line)
        if not ref:
            logger.warning('If it\'s related to fixing an issue, put Fix #number in title\n')
    for idx, i in enumerate(line):
        # ] } : must be followed by a space
        for j in [']', '}', ':']:
            if i == j:
                try:
                    assert line[idx + 1] == ' '
                    break
                except:
                    logger.info('%s%s: missing space after %s', line, yellow, j)
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
        # First word after the colon must be capitalized
        if i == ':':
            if line[idx + 1] == ' ' and line[idx + 2].islower() and line[idx + 2: idx + 5] != 'az ':
                index = idx + 2
            elif line[idx + 1] != ' ' and line[idx + 1].islower() and line[idx + 1: idx + 4] != 'az ':
                index = idx + 1
            else:
                continue
            logger.info('%s%s: should use capital letters after :', line, yellow)
            logger.error(' ' * index + '↑')
            error_flag = True
        # --xxx parameters must be enclosed in `, e.g., `--size`
        if i == '-' and line[idx + 1] == '-':
            param = '--'
            index = idx + 2
            while index < len(line) and line[index] != ' ':
                param += line[index]
                index += 1
            try:
                assert line[idx - 1] == '`'
            except:
                logger.info('%s%s: missing ` around %s', line, yellow, param)
                logger.error(' ' * idx + '↑' + ' ' * (index - idx - 2) + '↑')
                error_flag = True
    return error_flag


if __name__ == '__main__':
    main()
