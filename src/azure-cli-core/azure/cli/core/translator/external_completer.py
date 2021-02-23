# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from argcomplete.completers import FilesCompleter
from argcomplete.completers import DirectoriesCompleter


# this function will be hooked in azdev
def _build_external_completer_instance(cls, args, kwargs):
    return cls(*args, **kwargs)


def _external_completer_cls_wrapper(cls):
    def wrapper(*args, **kwargs):
        return _build_external_completer_instance(cls, args, kwargs)
    return wrapper


FilesCompleter = _external_completer_cls_wrapper(FilesCompleter)
DirectoriesCompleter = _external_completer_cls_wrapper(DirectoriesCompleter)
