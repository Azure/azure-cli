import getpass
from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
import azure.cli as cli

client = {}

def init_telemetry():
    try:
        instrumentation_key = 'eb6e9d3a-b6ee-41a6-804f-70e152fdfc36'

        global client #pylint: disable=global-statement
        client = TelemetryClient(instrumentation_key)

        client.context.application.id = 'Azure CLI'
        client.context.application.ver = cli.__version__
        client.context.user.id = hash(getpass.getuser())

        #enable(instrumentation_key)
    except Exception: #pylint: disable=broad-except
        # Never fail the command because of telemetry
        pass

def user_agrees_to_telemetry():
    # TODO: agreement, needs to take Y/N from the command line
    # and needs a "skip" param to not show (for scripts)
    return True

def telemetry_flush():
    try:
        client.flush()
    except Exception: #pylint: disable=broad-except
        # Never fail the command because of telemetry
        pass
