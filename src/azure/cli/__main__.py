import time
_import_time = time.perf_counter()

import sys

import azure.cli.main
from azure.cli._logging import logging

try:
    sys.exit(azure.cli.main.main(sys.argv[1:]))
finally:
    # Note: script time includes idle and network time
    logging.info('Execution time: %8.3fms', 1000 * (time.perf_counter() - _import_time))
