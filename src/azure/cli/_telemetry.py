import getpass
from applicationinsights import TelemetryClient
from applicationinsights.exceptions import enable
import azure.cli as cli

# event, exception, Trace, metric, message

class Telemetry(object): # pylint:disable=too-few-public-methods
    client = None

    @staticmethod
    def init_telemetry():
        instrumentation_key = 'eb6e9d3a-b6ee-41a6-804f-70e152fdfc36'

        Telemetry.client = TelemetryClient(instrumentation_key)

        Telemetry.client.context.application.id = 'Azure CLI'
        Telemetry.client.context.application.ver = cli.__version__
        Telemetry.client.context.user.id = hash(getpass.getuser())

        enable(instrumentation_key)

def user_agrees_to_telemetry():
    # TODO: agreement, needs to take Y/N from the command line
    # and needs a "skip" param to not show (for scripts)
    return True

def telemetry_log_event(name, properties=None, measurements=None):
    try:
        if Telemetry.client is None:
            return
        Telemetry.client.track_event(name, properties, measurements)
        Telemetry.client.flush()
    except Exception as e:
        #pass
        raise e

