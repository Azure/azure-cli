# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys
import threading
import unittest
from unittest import mock

from azure.cli.core.aaz._poller import AAZLROPoller


class TestAAZLROPoller(unittest.TestCase):

    def test_requests_imported_before_polling_thread(self):
        loaded = []
        real_start = threading.Thread.start

        def start(thread):
            loaded.append("requests" in sys.modules)
            real_start(thread)

        def polling_generator():
            yield from ()

        with mock.patch.dict(sys.modules), mock.patch.object(threading.Thread, "start", start):
            for name in [n for n in sys.modules if n == "requests" or n.startswith("requests.")]:
                del sys.modules[name]
            AAZLROPoller(polling_generator=polling_generator(), result_callback=None).wait()

        self.assertEqual(loaded, [True])


if __name__ == "__main__":
    unittest.main()
