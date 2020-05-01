# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import uuid
import timeit

from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.log import get_logger

from azure.cli.core import get_default_cli

import azure.cli.core.telemetry as telemetry

# Log the start time
start_time = timeit.default_timer()

# A workaround for https://bugs.python.org/issue32502 (https://github.com/Azure/azure-cli/issues/5184)
# If uuid1 raises ValueError, use uuid4 instead.
try:
    uuid.uuid1()
except ValueError:
    uuid.uuid1 = uuid.uuid4


logger = get_logger(__name__)


def cli_main(cli, args):
    return cli.invoke(args)


az_cli = get_default_cli()

telemetry.set_application(az_cli, ARGCOMPLETE_ENV_NAME)

# Log the init finish time
init_time = timeit.default_timer()

try:
    telemetry.start()

    exit_code = cli_main(az_cli, sys.argv[1:])

    if exit_code and exit_code != 0:
        telemetry.set_failure()
    else:
        telemetry.set_success()

    # Log the invoke finish time
    invoke_time = timeit.default_timer()

    sys.exit(exit_code)

except KeyboardInterrupt:
    telemetry.set_user_fault('keyboard interrupt')
    sys.exit(1)
except SystemExit as ex:  # some code directly call sys.exit, this is to make sure command metadata is logged
    exit_code = ex.code if ex.code is not None else 1

    try:
        # Log the invoke finish time
        invoke_time = timeit.default_timer()
    except NameError:
        pass

    raise ex

finally:
    telemetry.conclude()

    try:
        logger.info("Command ran in %.3f seconds (init: %.3f, invoke: %.3f)",
                    invoke_time - start_time, init_time - start_time, invoke_time - init_time)
    except NameError:
        pass
