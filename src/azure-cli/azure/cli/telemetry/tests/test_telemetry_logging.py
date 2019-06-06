# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import base64
import unittest
import tempfile
import logging
import logging.handlers

from azure.cli.telemetry.components.telemetry_logging import get_logger, LOGGER_NAME, config_logging_for_upload
from azure.cli.telemetry.const import TELEMETRY_LOG_NAME, TELEMETRY_LOG_DIR


class TestTelemetryLogging(unittest.TestCase):
    def test_create_logger(self):
        random_name = base64.b64encode(os.urandom(8)).decode('utf-8')
        logger = get_logger(random_name)

        self.assertEqual('{}.{}'.format(LOGGER_NAME, random_name), logger.name)

        logger.debug('come from {}'.format(random_name))


class TestTelemetryUploadLogging(unittest.TestCase):
    def setUp(self):
        self._original_handlers = logging.root.handlers
        self._original_level = logging.root.level
        del logging.root.handlers[:]

    def tearDown(self):
        for handler in logging.root.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if handler.stream:
                    handler.stream.close()

        del logging.root.handlers[:]
        logging.root.setLevel(self._original_level)
        for handler in self._original_handlers:
            logging.root.addHandler(handler)

    def test_config_logging_for_upload_process(self):
        temp_dir = tempfile.mkdtemp()
        random_name = base64.b64encode(os.urandom(8)).decode('utf-8')

        config_logging_for_upload(temp_dir)

        logger = get_logger(random_name)
        logger.info('come from {}'.format(random_name))

        log_file = os.path.join(temp_dir, TELEMETRY_LOG_DIR, TELEMETRY_LOG_NAME)
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, mode='r') as fq:
            content = fq.read().strip('\n')
            self.assertTrue(content.endswith(random_name),
                            'Log content {} does not contain {}'.format(content, random_name))

    def test_config_logging_for_upload_process_nonexist(self):
        temp_dir = tempfile.mktemp()
        self.assertFalse(os.path.isdir(temp_dir))

        random_name = base64.b64encode(os.urandom(8)).decode('utf-8')

        config_logging_for_upload(temp_dir)

        logger = get_logger(random_name)
        logger.info('come from {}'.format(random_name))

        log_file = os.path.join(temp_dir, TELEMETRY_LOG_DIR, TELEMETRY_LOG_NAME)
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, mode='r') as fq:
            content = fq.read().strip('\n')
            self.assertTrue(content.endswith(random_name),
                            'Log content {} does not contain {}'.format(content, random_name))


if __name__ == '__main__':
    unittest.main()
