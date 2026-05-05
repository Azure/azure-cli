# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import stat
import logging
import tempfile
import unittest

from azure.cli.core.azlogging import SecureFileHandler, SecureRotatingFileHandler


class TestSecureFileHandler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_secure_file_handler_writes_log(self):
        log_path = os.path.join(self.temp_dir, 'test.log')
        handler = SecureFileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('test_secure_file_handler')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info('test message')
            handler.flush()
            with open(log_path, 'r') as f:
                self.assertIn('test message', f.read())
        finally:
            logger.removeHandler(handler)
            handler.close()

    @unittest.skipIf(sys.platform == 'win32', 'POSIX file permissions not applicable on Windows')
    def test_secure_file_handler_permissions(self):
        log_path = os.path.join(self.temp_dir, 'secure.log')
        handler = SecureFileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('test_secure_file_handler_perms')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info('secret data')
            handler.flush()
            mode = os.stat(log_path).st_mode
            self.assertEqual(stat.S_IMODE(mode), 0o600)
        finally:
            logger.removeHandler(handler)
            handler.close()


class TestSecureRotatingFileHandler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_secure_rotating_file_handler_writes_log(self):
        log_path = os.path.join(self.temp_dir, 'rotating.log')
        handler = SecureRotatingFileHandler(log_path, maxBytes=1024, backupCount=2)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('test_secure_rotating_handler')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info('rotating test message')
            handler.flush()
            with open(log_path, 'r') as f:
                self.assertIn('rotating test message', f.read())
        finally:
            logger.removeHandler(handler)
            handler.close()

    @unittest.skipIf(sys.platform == 'win32', 'POSIX file permissions not applicable on Windows')
    def test_secure_rotating_file_handler_permissions(self):
        log_path = os.path.join(self.temp_dir, 'rotating_secure.log')
        handler = SecureRotatingFileHandler(log_path, maxBytes=1024, backupCount=2)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('test_secure_rotating_handler_perms')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info('secret rotating data')
            handler.flush()
            mode = os.stat(log_path).st_mode
            self.assertEqual(stat.S_IMODE(mode), 0o600)
        finally:
            logger.removeHandler(handler)
            handler.close()

    @unittest.skipIf(sys.platform == 'win32', 'POSIX file permissions not applicable on Windows')
    def test_secure_rotating_file_handler_rotation_preserves_permissions(self):
        log_path = os.path.join(self.temp_dir, 'rotate_perm.log')
        handler = SecureRotatingFileHandler(log_path, maxBytes=50, backupCount=2)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('test_secure_rotating_rotation')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            # Write enough data to trigger at least one rotation
            for i in range(20):
                logger.info('message %d with enough length to rotate', i)
            handler.flush()

            # Check that the main log file has 0o600 permissions
            mode = os.stat(log_path).st_mode
            self.assertEqual(stat.S_IMODE(mode), 0o600)

            # Check backup files have 0o600 permissions too
            for suffix in ['.1', '.2']:
                backup = log_path + suffix
                if os.path.exists(backup):
                    mode = os.stat(backup).st_mode
                    self.assertEqual(stat.S_IMODE(mode), 0o600,
                                     f"Backup file {backup} has wrong permissions")
        finally:
            logger.removeHandler(handler)
            handler.close()


if __name__ == '__main__':
    unittest.main()
