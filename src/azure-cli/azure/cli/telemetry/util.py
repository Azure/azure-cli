# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import stat
import logging
import logging.handlers
from datetime import datetime

from azure.cli.telemetry.const import TELEMETRY_NOTE_NAME, MANDATORY_WAIT_PERIOD


def should_upload(config_dir):
    """Returns True if it is the right moment to add telemetry.
    Before the client request a telemetry add process, it can invoke this method to test if it is the right moment.
    The conditions are:
        1. The telemetry.txt file doesn't exist; OR
        2. The telemetry.txt file is a regular file AND there have been enough time passed since last add.
    """
    logger = logging.getLogger('telemetry.check')

    telemetry_note_path = os.path.join(config_dir, TELEMETRY_NOTE_NAME)
    if not os.path.exists(telemetry_note_path):
        logger.info('Positive: The %s does not exist.', telemetry_note_path)
        return True

    file_stat = os.stat(telemetry_note_path)
    if not stat.S_ISREG(file_stat.st_mode):
        logger.warning('Negative: The %s is not a regular file.', telemetry_note_path)
        return False

    modify_time = datetime.fromtimestamp(file_stat.st_mtime)
    if datetime.now() - modify_time < MANDATORY_WAIT_PERIOD:
        logger.warning('Negative: The %s was modified at %s, which in less than %f s',
                       telemetry_note_path, modify_time, MANDATORY_WAIT_PERIOD.total_seconds())
        return False

    logger.info('Returns Positive.')
    return True


def save_payload(config_dir, payload):
    """
    Save a telemetry payload to the telemetry cache directory under the given configuration directory
    """
    logger = logging.getLogger('telemetry.save')

    if payload:
        cache_saver = _create_rotate_file_logger(config_dir)
        if cache_saver:
            cache_saver.info(payload)
            logger.info('Save telemetry record of length %d in cache', len(payload))

            return True
    return False


def _create_rotate_file_logger(log_dir):
    cache_name = os.path.join(log_dir, 'telemetry', 'cache')
    try:
        if not os.path.exists(os.path.dirname(cache_name)):
            os.makedirs(os.path.dirname(cache_name))

        handler = logging.handlers.RotatingFileHandler(cache_name, maxBytes=128 * 1024, backupCount=100)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(fmt='%(asctime)s,%(message)s',
                                               datefmt='%Y-%m-%dT%H:%M:%S'))

        logger = logging.Logger(name='telemetry_cache', level=logging.INFO)
        logger.addHandler(handler)
        return logger
    except OSError as err:
        logging.getLogger('telemetry.save').warning('Fail to create telemetry cache directory for %s. Reason %s.',
                                                    cache_name,
                                                    err)
        return None
