import sys

import azure.cli.main

from azure.cli._telemetry import init_telemetry, user_agrees_to_telemetry, telemetry_flush

try:
    try:
        if user_agrees_to_telemetry():
            init_telemetry()
    except Exception: #pylint: disable=broad-except
        pass

    sys.exit(azure.cli.main.main(sys.argv[1:]))
finally:
    telemetry_flush()
