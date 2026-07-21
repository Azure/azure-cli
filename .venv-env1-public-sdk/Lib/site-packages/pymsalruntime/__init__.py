# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import platform

if platform.system() == "Linux":
    import os
    import ctypes

    library_path = os.path.join(os.path.dirname(__file__), "libmsalruntime.so")
    ctypes.CDLL(library_path)

import pymsalruntime.pymsalruntime as pymsalrt
import atexit

pymsalrt._startup_msalruntime()
atexit.register(pymsalrt._shutdown_msalruntime)

from pymsalruntime.pymsalruntime import *
