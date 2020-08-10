import collections

from django.conf import settings
import applicationinsights

ApplicationInsightsSettings = collections.namedtuple("ApplicationInsightsSettings", [
    "ikey",
    "channel_settings",
    "use_view_name",
    "record_view_arguments",
    "log_exceptions"])

ApplicationInsightsChannelSettings = collections.namedtuple("ApplicationInsightsChannelSettings", [
    "send_interval",
    "send_time",
    "endpoint"])

def load_settings():
    if hasattr(settings, "APPLICATION_INSIGHTS"):
        config = settings.APPLICATION_INSIGHTS
    elif hasattr(settings, "APPLICATIONINSIGHTS"):
        config = settings.APPLICATIONINSIGHTS
    else:
        config = {}

    if not isinstance(config, dict):
        config = {}

    return ApplicationInsightsSettings(
        ikey=config.get("ikey"),
        use_view_name=config.get("use_view_name", False),
        record_view_arguments=config.get("record_view_arguments", False),
        log_exceptions=config.get("log_exceptions", True),
        channel_settings=ApplicationInsightsChannelSettings(
            endpoint=config.get("endpoint"),
            send_interval=config.get("send_interval"),
            send_time=config.get("send_time")))

saved_clients = {}
saved_channels = {}

def create_client(aisettings=None):
    global saved_clients, saved_channels

    if aisettings is None:
        aisettings = load_settings()

    if aisettings in saved_clients:
        return saved_clients[aisettings]

    channel_settings = aisettings.channel_settings

    if channel_settings in saved_channels:
        channel = saved_channels[channel_settings]
    else:
        if channel_settings.endpoint is not None:
            sender = applicationinsights.channel.AsynchronousSender(service_endpoint_uri=channel_settings.endpoint)
        else:
            sender = applicationinsights.channel.AsynchronousSender()

        if channel_settings.send_time is not None:
            sender.send_time = channel_settings.send_time
        if channel_settings.send_interval is not None:
            sender.send_interval = channel_settings.send_interval

        queue = applicationinsights.channel.AsynchronousQueue(sender)
        channel = applicationinsights.channel.TelemetryChannel(None, queue)
        saved_channels[channel_settings] = channel

    ikey = aisettings.ikey
    if ikey is None:
        return dummy_client("No ikey specified")

    client = applicationinsights.TelemetryClient(aisettings.ikey, channel)
    saved_clients[aisettings] = client
    return client

def dummy_client(reason):
    """Creates a dummy channel so even if we're not logging telemetry, we can still send
    along the real object to things that depend on it to exist"""

    sender = applicationinsights.channel.NullSender()
    queue = applicationinsights.channel.SynchronousQueue(sender)
    channel = applicationinsights.channel.TelemetryChannel(None, queue)
    return applicationinsights.TelemetryClient("00000000-0000-0000-0000-000000000000", channel)
