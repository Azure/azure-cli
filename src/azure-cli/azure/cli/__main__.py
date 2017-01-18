# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os

import azure.cli.main
import azure.cli.core.telemetry as telemetry

try:
    telemetry.start()
    args = sys.argv[1:]

    # Check if we are in argcomplete mode - if so, we
    # need to pick up our args from environment variables
    if os.environ.get('_ARGCOMPLETE'):
        comp_line = os.environ.get('COMP_LINE')
        if comp_line:
            args = comp_line.split()[1:]

    exit_code = azure.cli.main.main(args)
    if exit_code and exit_code != 0:
        telemetry.set_failure()
    else:
        telemetry.set_success()

    sys.exit(exit_code)
except KeyboardInterrupt:
    telemetry.set_user_fault('keyboard interrupt')
    sys.exit(1)
finally:
    telemetry.conclude()
