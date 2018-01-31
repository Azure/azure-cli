# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# gather all the pylint disable statements

import os
import re
import itertools
import tabulate
from ..utilities.path import get_repo_root


def get_files(root):
    for root, dirs, files in os.walk('src'):
        for py_file in files:
            if py_file.endswith('.py'):
                yield os.path.join(root, py_file)


def get_rules(file_path):
    rgx = re.compile('# pylint: disable=(\w|-|,|\s)+')
    with open(file_path) as f:
        for index, l in enumerate(f.readlines()):
            if not l:
                break

            m = rgx.search(l)
            if m:
                rules = (r.strip() for r in m.group(0).strip().split('=')[1].split(','))
                for r in rules:
                    yield r, index, file_path


def get_all_rules(root):
    return itertools.chain.from_iterable(get_rules(f) for f in get_files('src'))


def group_by_rules(rules_iter):
    sortiter = sorted(rules_iter, key=lambda each: each[0])
    for k, g in itertools.groupby(sortiter, lambda each: each[0]):
        group = list(g)
        yield k, len(group)


def group_by_files(rules_iter):
    sortiter = sorted(rules_iter, key=lambda each: each[2])
    for k, g in itertools.groupby(sortiter, lambda each: each[2]):
        group = list(g)
        count = len(group)
        with open(k, 'r') as f:
            line_number = len(f.readlines())

        yield k, count, line_number, int(line_number / count)


def main():
    src_folder = os.path.join(get_repo_root(), 'src')
    all_rules = [e for e in get_all_rules(src_folder)]

    with open('pylint_report.txt', 'w') as f:
        f.write('GROUP BY RULES\n')
        f.writelines(tabulate.tabulate(sorted(group_by_rules(all_rules), key=lambda each: each[1], reverse=True),
                                       headers=('rule', 'count')))

        f.write('\n\nGROUP BY FILES\n')
        f.writelines(tabulate.tabulate(sorted(group_by_files(all_rules), key=lambda each: each[1], reverse=True),
                                       headers=('file', 'pylint count', 'total lines', 'every n line')))

    with open('pylint_all_disables.csv', 'w') as f:
        for r in all_rules:
            f.write('{},{},{}\n'.format(*r))


if __name__ == '__main__':
    main()
