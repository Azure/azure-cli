# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import logging.handlers


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
