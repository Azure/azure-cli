# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


def test_cmd(args):
    from azdev.__main__ import main
    import sys

    sys.argv = [sys.executable] + args.split()
    return main()
