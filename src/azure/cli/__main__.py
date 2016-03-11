import sys
import os
import signal

import azure.cli.main

signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(1))

if os.name != 'nt':
    # can't call Windows with SIGPIPE
    signal.signal(signal.SIGPIPE, lambda signum, frame: sys.exit(1))

sys.exit(azure.cli.main.main(sys.argv[1:]))
