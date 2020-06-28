from .QueueBase import QueueBase
from threading import Event

class AsynchronousQueue(QueueBase):
    """An asynchronous queue for use in conjunction with the :class:`AsynchronousSender`. The queue
    will notify the sender that it needs to pick up items when it reaches :func:`max_queue_length`, or
    when the consumer calls :func:`flush` via the :func:`flush_notification` event.
    """
    def __init__(self, sender):
        """Initializes a new instance of the class.

        Args:
            sender (:class:`SenderBase`) the sender object that will be used in conjunction with this queue.
        """
        self._flush_notification = Event()
        QueueBase.__init__(self, sender)

    @property
    def flush_notification(self):
        """The flush notification :class:`Event` that the :func:`sender` will use to get notified
        that a flush is needed.

        Returns:
            :class:`Event`. object that the :func:`sender` can wait on.
        """
        return self._flush_notification

    def put(self, item):
        """Adds the passed in item object to the queue and notifies the :func:`sender` to start an asynchronous
        send operation by calling :func:`start`.

        Args:
            item (:class:`contracts.Envelope`) the telemetry envelope object to send to the service.
        """
        QueueBase.put(self, item)
        if self.sender:
            self.sender.start()

    def flush(self):
        """Flushes the current queue by notifying the :func:`sender` via the :func:`flush_notification` event.
        """
        self._flush_notification.set()
        if self.sender:
            self.sender.start()
