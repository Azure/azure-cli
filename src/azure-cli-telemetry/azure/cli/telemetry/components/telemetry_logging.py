# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import logging.handlers

from ..const import TELEMETRY_LOG_NAME, TELEMETRY_LOG_DIR

LOGGER_NAME = 'telemetry'


def config_logging_for_upload(config_dir):
    """Set up a logging handler for the logger during the upload process.

    The upload process is an independent process apart from the main CLI process. Its stderr and stdout are both
    redirected to /dev/null. Therefore stream handler is not applicable. This method will set up a telemetry logging
    file under the user profile configuration dir, which is specified by the `config_dir` parameter, to save the
    logging records.

    The method should be called once in the entry of the upload process.
    """
    folder = _ensure_telemetry_log_folder(config_dir)
    if folder:
        handler = logging.handlers.RotatingFileHandler(os.path.join(folder, TELEMETRY_LOG_NAME),
                                                       maxBytes=10 * 1024 * 1024, backupCount=5)
        del logging.root.handlers[:]
        formatter = logging.Formatter('%(process)d : %(asctime)s : %(levelname)s : %(name)s : %(message)s', None)
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.DEBUG)


def get_logger(section_name):
    """Returns a logger for the given sub section. The logger's name will reflect that this logger is from the telemetry
    module."""
    return logging.getLogger('{}.{}'.format(LOGGER_NAME, section_name))


def _ensure_telemetry_log_folder(config_dir):
    try:
        ret = os.path.join(config_dir, TELEMETRY_LOG_DIR)
        if not os.path.isdir(ret):
            os.makedirs(ret)
        return ret
    except (OSError, IOError, TypeError):
        return None
