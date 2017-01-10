# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os

import azure.cli.main
import azure.cli.core.telemetry as telemetry

try:
    args = sys.argv[1:]

    # Check if we are in argcomplete mode - if so, we
    # need to pick up our args from environment variables
    if os.environ.get('_ARGCOMPLETE'):
        comp_line = os.environ.get('COMP_LINE')
        if comp_line:
            args = comp_line.split()[1:]

    sys.exit(azure.cli.main.main(args))
except KeyboardInterrupt:
    telemetry.log_telemetry('keyboard interrupt')
    sys.exit(1)
finally:
    try:
        telemetry.flush_telemetry()
    except Exception:  # pylint: disable=broad-except
        pass
