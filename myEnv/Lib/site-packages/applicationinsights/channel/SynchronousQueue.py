from .QueueBase import QueueBase

class SynchronousQueue(QueueBase):
    """A synchronous queue for use in conjunction with the :class:`SynchronousSender`. The queue will call
    :func:`send` on :func:`sender` when it reaches :func:`max_queue_length`, or when the consumer calls
    :func:`flush`.

    .. code:: python

        from application_insights.channel import SynchronousQueue
        queue = SynchronousQueue(None)
        queue.max_queue_length = 1
        queue.put(1)
    """
    def __init__(self, sender):
        """Initializes a new instance of the class.

        Args:
            sender (:class:`SenderBase`) the sender object that will be used in conjunction with this queue.
        """
        QueueBase.__init__(self, sender)

    def flush(self):
        """Flushes the current queue by by calling :func:`sender`'s :func:`send` method.
        """
        local_sender = self.sender
        if not local_sender:
            return
        while True:
            # get at most send_buffer_size items and send them
            data = []
            while len(data) < local_sender.send_buffer_size:
                item = self.get()
                if not item:
                    break
                data.append(item)
            if len(data) == 0:
                break
            local_sender.send(data)
