import logging
import sys
import time

_import_time = time.perf_counter()

import azure.cli.main
try:
    sys.exit(azure.cli.main.main(sys.argv[1:]))
finally:
    # Process time includes Python engine startup
    # Script time includes azure.cli module only
    logging.debug('Process time: %8.3fms', 1000 * time.process_time())
    logging.debug('Script time:  %8.3fms', 1000 * (time.perf_counter() - _import_time))
