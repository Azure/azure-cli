import time
_import_time = time.perf_counter()

import logging
import sys

import azure.cli.main
try:
    sys.exit(azure.cli.main.main(sys.argv[1:]))
finally:
    # CPU time includes startup
    # Script time includes idle time, and azure.cli module only
    logging.debug('CPU time:    %8.3fms', 1000 * time.process_time())
    logging.debug('Script time: %8.3fms', 1000 * (time.perf_counter() - _import_time))
