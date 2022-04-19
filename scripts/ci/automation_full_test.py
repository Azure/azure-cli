#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import subprocess
import sys
from azdev.utilities import get_path_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
profile = sys.argv[1]
serial_modules = sys.argv[2].split()


class AutomaticScheduling(object):

    def __init__(self):
        self.modules = {}
        self.serial_modules = serial_modules
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        # only get modules and core, ignore extensions
        self.modules = {**result['mod'], **result['core']}

    def run_modules(self):
        # divide all modules into parallel or serial execution
        error_flag = False
        serial_tests = []
        parallel_tests = []
        for k, v in self.modules.items():
            if k in self.serial_modules:
                serial_tests.append(k)
            else:
                parallel_tests.append(k)
        if serial_tests:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + \
                  serial_tests + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            logger.info(cmd)
            try:
                subprocess.run(cmd)
            except subprocess.CalledProcessError:
                error_flag = True
        if parallel_tests:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + \
                  parallel_tests + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            logger.info(cmd)
            try:
                subprocess.run(cmd)
            except subprocess.CalledProcessError:
                error_flag = True
        return error_flag


def main():
    logger.info("Start automation full test ...\n")
    autoschduling = AutomaticScheduling()
    autoschduling.get_all_modules()
    sys.exit(1) if autoschduling.run_modules() else sys.exit(0)


if __name__ == '__main__':
    main()
