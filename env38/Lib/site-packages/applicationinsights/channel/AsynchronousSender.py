from .SenderBase import SenderBase
from threading import Lock, Thread

class AsynchronousSender(SenderBase):
    """An asynchronous sender that works in conjunction with the :class:`AsynchronousQueue`. The sender object will
    start a worker thread that will pull items from the :func:`queue`. The thread will be created when the client
    calls :func:`start` and will check for queue items every :func:`send_interval` seconds. The worker thread can
    also be forced to check the queue by setting the :func:`flush_notification` event.

    - If no items are found, the thread will go back to sleep.
    - If items are found, the worker thread will send items to the specified service in batches of :func:`send_buffer_size`.

    If no queue items are found for :func:`send_time` seconds, the worker thread will shut down (and :func:`start` will
    need  to be called again).
    """
    def __init__(self, service_endpoint_uri='https://dc.services.visualstudio.com/v2/track'):
        """Initializes a new instance of the class.

        Args:
            sender (String) service_endpoint_uri the address of the service to send telemetry data to.
        """
        self._send_interval = 1.0
        self._send_remaining_time = 0
        self._send_time = 3.0
        self._lock_send_remaining_time = Lock()
        SenderBase.__init__(self, service_endpoint_uri)

    @property
    def send_interval(self):
        """The time span in seconds at which the the worker thread will check the :func:`queue` for items (defaults to: 1.0).

        Args:
            value (int) the interval in seconds.

        Returns:
            int. the interval in seconds.
        """
        return self._send_interval

    @send_interval.setter
    def send_interval(self, value):
        """The time span in seconds at which the the worker thread will check the :func:`queue` for items (defaults to: 1.0).

        Args:
            value (int) the interval in seconds.

        Returns:
            int. the interval in seconds.
        """
        self._send_interval = value

    @property
    def send_time(self):
        """The time span in seconds at which the the worker thread will check the :func:`queue` for items (defaults to: 1.0).

        Args:
            value (int) the interval in seconds.

        Returns:
            int. the interval in seconds.
        """
        return self._send_time

    @send_time.setter
    def send_time(self, value):
        """The time span in seconds at which the the worker thread will check the :func:`queue` for items (defaults to: 1.0).

        Args:
            value (int) the interval in seconds.

        Returns:
            int. the interval in seconds.
        """
        self._send_time = value

    def start(self):
        """Starts a new sender thread if none is not already there
        """
        with self._lock_send_remaining_time:
            if self._send_remaining_time <= 0.0:
                local_send_interval = self._send_interval
                if self._send_interval < 0.1:
                    local_send_interval = 0.1
                self._send_remaining_time = self._send_time
                if self._send_remaining_time < local_send_interval:
                    self._send_remaining_time = local_send_interval
                thread = Thread(target=self._run)
                thread.daemon = True
                thread.start()

    def stop(self):
        """Gracefully stops the sender thread if one is there.
        """
        with self._lock_send_remaining_time:
            self._send_remaining_time = 0.0

    def _run(self):
        # save the queue locally
        local_queue = self._queue
        if not local_queue:
            self.stop()
            return

        # fix up the send interval (can't be lower than 100ms)
        local_send_interval = self._send_interval
        if self._send_interval < 0.1:
            local_send_interval = 0.1
        local_send_time = self._send_time
        if local_send_time < local_send_interval:
            local_send_time = local_send_interval
        while True:
            while True:
                # get at most send_buffer_size items from the queue
                counter = self._send_buffer_size
                data = []
                while counter > 0:
                    item = local_queue.get()
                    if not item:
                        break
                    data.append(item)
                    counter -= 1

                # if we didn't get any items from the queue, we're done here
                if len(data) == 0:
                    break

                # reset the send time
                with self._lock_send_remaining_time:
                    self._send_remaining_time = local_send_time

                # finally send the data
                self.send(data)

            # wait at most send_interval (or until we get signalled)
            result = local_queue.flush_notification.wait(local_send_interval)
            if result:
                local_queue.flush_notification.clear()
                continue

            # decrement the remaining time
            local_remaining_time = 0
            with self._lock_send_remaining_time:
                self._send_remaining_time -= local_send_interval
                local_remaining_time = self._send_remaining_time

            if local_remaining_time <= 0:
                break
