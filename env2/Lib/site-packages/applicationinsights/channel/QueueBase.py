try:
    # Python 2.x
    from Queue import Queue, Empty
except ImportError:
    # Python 3.x
    from queue import Queue, Empty

try:
    from persistqueue import Empty as PersistEmpty
    from persistqueue import Queue as PersistQueue
except ImportError:
    PersistEmpty = Empty
    PersistQueue = None


class QueueBase(object):
    """The base class for all types of queues for use in conjunction with an implementation of :class:`SenderBase`.

    The queue will notify the sender that it needs to pick up items when it reaches :func:`max_queue_length`,
    or when the consumer calls :func:`flush`.
    """
    def __init__(self, sender, persistence_path=''):
        """Initializes a new instance of the class.

        Args:
            sender (:class:`SenderBase`) the sender object that will be used in conjunction with this queue.
            persistence_path (str) if set, persist the queue on disk into the provided directory.
        """
        if persistence_path and PersistQueue is None:
            raise ValueError('persistence_path argument requires persist-queue dependency to be installed')
        elif persistence_path:
            self._queue = PersistQueue(persistence_path)
        else:
            self._queue = Queue()

        self._persistence_path = persistence_path
        self._max_queue_length = 500
        self._sender = sender
        if sender:
            self._sender.queue = self

    @property
    def max_queue_length(self):
        """The maximum number of items that will be held by the queue before the queue will call the :func:`flush`
        method.

        Args:
            value (int). the maximum queue length. The minimum allowed value is 1.

        Returns:
            int. the maximum queue size. (defaults to: 500)
        """
        return self._max_queue_length

    @max_queue_length.setter
    def max_queue_length(self, value):
        """The maximum number of items that will be held by the queue before the queue will call the :func:`flush`
        method.

        Args:
            value (int): the maximum queue length. The minimum allowed value is 1.

        Returns:
            int. the maximum queue size. (defaults to: 500)
        """
        if value < 1:
            value = 1
        self._max_queue_length = value

    @property
    def sender(self):
        """The sender that is associated with this queue that this queue will use to send data to the service.

        Returns:
            :class:`SenderBase`. the sender object.
        """
        return self._sender

    def put(self, item):
        """Adds the passed in item object to the queue and calls :func:`flush` if the size of the queue is larger
        than :func:`max_queue_length`. This method does nothing if the passed in item is None.

        Args:
            item (:class:`contracts.Envelope`) item the telemetry envelope object to send to the service.
        """
        if not item:
            return
        self._queue.put(item)
        if self._queue.qsize() >= self._max_queue_length:
            self.flush()

    def get(self):
        """Gets a single item from the queue and returns it. If the queue is empty, this method will return None.

        Returns:
            :class:`contracts.Envelope`. a telemetry envelope object or None if the queue is empty.
        """
        try:
            item = self._queue.get_nowait()
        except (Empty, PersistEmpty):
            return None

        if self._persistence_path:
            self._queue.task_done()

        return item

    def flush(self):
        """Flushes the current queue by notifying the {#sender}. This method needs to be overridden by a concrete
        implementations of the queue class.
        """
        pass