# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os
import sys

try:
    filename = sys.argv[1]
except IndexError:
    filename = 'log.txt'

try:
    dest_file = sys.argv[2]
except IndexError:
    dest_file = 'log_scrub.txt'

with open(filename) as f:
    lines = f.readlines()
    count = 0
    final_lines = []
    for line in lines:
        if '... ERROR' in line or '... FAIL' in line:
            line = line.replace('(', '')
            line = line.replace(')', '')
            try:
                test_name, test_path, _, _ = line.split(' ')
                path_comps = test_path.split('.')
                path_file = path_comps[-2]
                path_class = path_comps[-1]
                module_name = path_comps[-4]
                line = 'run_tests --module {} --test {}.{}.{}\n'.format(module_name, path_file, path_class, test_name)
            except:
                pass
            final_lines.append(line)

with open(dest_file, 'w') as f:
    for line in final_lines:
        f.write(line + os.linesep)
