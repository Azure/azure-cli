import datetime
import sys

from .SynchronousQueue import SynchronousQueue
from .SynchronousSender import SynchronousSender
from .TelemetryContext import TelemetryContext
from applicationinsights.channel import contracts

platform_moniker = 'py2'
if sys.version_info >= (3, 0):
    platform_moniker = 'py3'

# set up internal context
internal_context = contracts.Internal()
internal_context.sdk_version = platform_moniker + ':0.11.10'


class TelemetryChannel(object):
    """The telemetry channel is responsible for constructing a :class:`contracts.Envelope` object from the passed in
    data and specified telemetry context.

    .. code:: python

        from application_insights.channel import TelemetryChannel, contracts
        channel = TelemetryChannel()
        event = contracts.EventData()
        event.name = 'My event'
        channel.write(event)
    """

    def __init__(self, context=None, queue=None):
        """Initializes a new instance of the class.

        Args:
            context (:class:`TelemetryContext') the telemetry context to use when sending telemetry data.\n
            queue (:class:`QueueBase`) the queue to enqueue the resulting :class:`contracts.Envelope` to.
        """
        self._context = context or TelemetryContext()
        self._queue = queue or SynchronousQueue(SynchronousSender())

    @property
    def context(self):
        """The context associated with this channel. All :class:`contracts.Envelope` objects created by this channel
        will use this value if it's present or if none is specified as part of the :func:`write` call.

        Returns:
            (:class:`TelemetryContext`). the context instance (defaults to: TelemetryContext())
        """
        return self._context

    @property
    def queue(self):
        """The queue associated with this channel. All :class:`contracts.Envelope` objects created by this channel
        will be pushed to this queue.

        Returns:
            (:class:`QueueBase`). the queue instance (defaults to: SynchronousQueue())
        """
        return self._queue

    @property
    def sender(self):
        """The sender associated with this channel. This instance will be used to transmit telemetry to the service.

        Returns:
            (:class:`SenderBase`). the sender instance (defaults to: SynchronousSender())
        """
        return self._queue.sender

    def flush(self):
        """Flushes the enqueued data by calling :func:`flush` on :func:`queue`.
        """
        self._queue.flush()

    def write(self, data, context=None):
        """Enqueues the passed in data to the :func:`queue`. If the caller specifies a context as well, it will
        take precedence over the instance in :func:`context`.

        Args:
            data (object). data the telemetry data to send. This will be wrapped in an :class:`contracts.Envelope`
                before being enqueued to the :func:`queue`.
            context (:class:`TelemetryContext`). context the override context to use when constructing the
                :class:`contracts.Envelope`.
        """
        local_context = context or self._context
        if not local_context:
            raise Exception('Context was required but not provided')

        if not data:
            raise Exception('Data was required but not provided')

        envelope = contracts.Envelope()
        envelope.name = data.ENVELOPE_TYPE_NAME
        envelope.time = datetime.datetime.utcnow().isoformat() + 'Z'
        envelope.ikey = local_context.instrumentation_key
        tags = envelope.tags
        for prop_context in [self._context, context]:
            if not prop_context:
                continue
            for key, value in self._write_tags(prop_context):
                tags[key] = value
        envelope.data = contracts.Data()
        envelope.data.base_type = data.DATA_TYPE_NAME
        for prop_context in [context, self._context]:
            if not prop_context:
                continue
            if hasattr(data, 'properties') and prop_context.properties:
                properties = data.properties
                for key in prop_context.properties:
                    if key not in properties:
                        properties[key] = prop_context.properties[key]
        envelope.data.base_data = data

        self._queue.put(envelope)

    def _write_tags(self, context):
        for item in [internal_context,
                     context.device, context.cloud, context.application, context.user,
                     context.session, context.location, context.operation]:
            if not item:
                continue
            for pair in item.write().items():
                yield pair
