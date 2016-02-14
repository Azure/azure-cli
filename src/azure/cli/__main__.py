import time
_import_time = time.perf_counter()

import logging
import sys

import azure.cli.main
try:
    sys.exit(azure.cli.main.main(sys.argv[1:]))
finally:
    # Note: script time includes idle time
    logging.info('Script time: %8.3fms', 1000 * (time.perf_counter() - _import_time))
