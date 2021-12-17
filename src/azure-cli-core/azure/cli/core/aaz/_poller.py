from azure.core.polling.base_polling import LROBasePolling
from azure.core.polling import NoPolling, LROPoller
import threading
from azure.core.tracing.common import with_current_context
import uuid


class AAZNoPolling(NoPolling):
    pass


class AAZBasePolling(LROBasePolling):
    pass


class AAZLROPoller(LROPoller):

    def __init__(self, polling_method, result_callback):
        self._callbacks = []
        self._polling_method = polling_method
        self._result_callback = result_callback

        self._thread = None
        self._done = None
        self._exception = None
        if not self._polling_method.finished():
            self._done = threading.Event()
            self._thread = threading.Thread(
                target=with_current_context(self._start),
                name="LROPoller({})".format(uuid.uuid4()))
            self._thread.daemon = True
            self._thread.start()

    def result(self, *args, **kwargs):
        resource = super(AAZLROPoller, self).result(*args, **kwargs)
        if self._result_callback:
            return self._result_callback(resource)
        else:
            return resource
