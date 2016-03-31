import sys
import os

import azure.cli.main

from azure.cli._telemetry import init_telemetry, user_agrees_to_telemetry, telemetry_flush

try:
    try:
        if user_agrees_to_telemetry():
            init_telemetry()
    except Exception: #pylint: disable=broad-except
        pass

    args = sys.argv[1:]
    
    # Check if we are in argcomplete mode - if so, we
    # need to pick up our args from environment variables
    if os.environ.get('_ARGCOMPLETE'):
        comp_line = os.environ.get('COMP_LINE')
        if comp_line:
            args = comp_line.split()[1:]
            
    sys.exit(azure.cli.main.main(args))
finally:
    telemetry_flush()
