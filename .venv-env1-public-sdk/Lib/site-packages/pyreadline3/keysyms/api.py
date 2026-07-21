# -*- coding: utf-8 -*-
# *****************************************************************************
#     Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#     Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************


from ..py3k_compat import is_ironpython

if is_ironpython:
    try:
        from .ironpython_keysyms import make_key_press, make_key_symbol
    except ImportError as e:
        raise ImportError("Could not import keysym for local ironpython version") from e
else:
    try:
        from .keysyms import make_key_press, make_key_symbol
    except ImportError as e:
        raise ImportError("Could not import keysym for local python version") from e

__all__ = [
    "make_key_press",
    "make_key_symbol",
]
