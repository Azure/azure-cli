# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import sys
import automation.verify
import automation.style
import automation.tests
import automation.cli_linter


def main():
    parser = argparse.ArgumentParser(prog='azdev')

    sub_parser = parser.add_subparsers(title='sub commands')
    automation.verify.init_args(sub_parser)
    automation.style.init_args(sub_parser)
    automation.tests.init_args(sub_parser)
    automation.cli_linter.init_args(sub_parser)

    if sys.argv[1:]:
        args = parser.parse_args()
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
