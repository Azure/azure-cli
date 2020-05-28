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

try:
    telemetry.start()
    start_time = timeit.default_timer()

    exit_code = cli_main(az_cli, sys.argv[1:])

    if exit_code and exit_code != 0:
        if az_cli.result.error is not None and not telemetry.has_exceptions():
            telemetry.set_exception(az_cli.result.error, fault_type='')
        telemetry.set_failure()
    else:
        telemetry.set_success()

    elapsed_time = timeit.default_timer() - start_time

    sys.exit(exit_code)

except KeyboardInterrupt:
    telemetry.set_user_fault('keyboard interrupt')
    sys.exit(1)
except SystemExit as ex:  # some code directly call sys.exit, this is to make sure command metadata is logged
    exit_code = ex.code if ex.code is not None else 1

    try:
        elapsed_time = timeit.default_timer() - start_time
    except NameError:
        pass

    raise ex

finally:
    telemetry.conclude()

    try:
        logger.info("command ran in %.3f seconds.", elapsed_time)
    except NameError:
        pass
