# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Validate the embedded interpreter before copying it into an MSI or ZIP."""

import argparse
import re
import struct
import sys
import sysconfig


def python_version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise argparse.ArgumentTypeError("expected a Python version in major.minor.patch format")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected_version", type=python_version,
                        help="exact Python version configured by the packaging build")
    expected_version = parser.parse_args(argv).expected_version
    actual_version = ".".join(map(str, sys.version_info[:3]))
    platform = sysconfig.get_platform()
    if (actual_version != expected_version or platform != "win-amd64"
            or struct.calcsize("P") != 8):
        print(
            f"Unsupported embedded Python: {actual_version} ({platform}). "
            f"Expected Python {expected_version} (win-amd64).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
