# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

__version__ = "1.0.1"

from .core import AzureDLFileSystem
from .multithread import ADLDownloader

# Set default logging handler
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
