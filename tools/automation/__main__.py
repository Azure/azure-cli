# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import sys
import automation.verify
import automation.clibuild

def main():
    parser = argparse.ArgumentParser(prog='Azure CLI build tools')

    sub_parser = parser.add_subparsers(title='azure cli tools sub commands')
    automation.verify.init_args(sub_parser)
    automation.clibuild.init_args(sub_parser)

    if sys.argv[1:]:
        args = parser.parse_args()
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

