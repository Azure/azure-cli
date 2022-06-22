# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._base import AAZBaseValue


class AAZArgBrowser:
    """Argument Browser is used to access the data of argument."""

    @classmethod
    def create(cls, arg):
        assert isinstance(arg, AAZBaseValue)
        return cls(arg_value=arg, arg_data=arg.to_serialized_data())

    def __init__(self, arg_value, arg_data, parent=None):
        assert isinstance(arg_value, AAZBaseValue)
        self._arg_value = arg_value
        self._arg_data = arg_data  # data should be the serialized data of value
        self._parent = parent

    def get_prop(self, key):
        """The sub property argument by key. The return value will be an Argument Browser as well."""
        if key is None or key == '.':
            return self

        if key.startswith('..'):
            if self._parent is None:
                raise ValueError(f"Invalid Key: '{key}' : parent is None")
            return self._parent.get(key[1:])

        if key.startswith('.'):
            names = key[1:].split('.', maxsplit=1)
            prop_name = names[0]
            if self._arg_data is None or prop_name not in self._arg_data:
                return None
            sub_value = self._arg_value[prop_name]
            sub_data = self._arg_data[prop_name]
            sub_browser = AAZArgBrowser(sub_value, sub_data, parent=self)
            if len(names) == 1:
                return sub_browser
            assert len(names) == 2
            return sub_browser.get_prop(f'.{names[1]}')

        raise NotImplementedError()

    def get_elements(self):
        """Iter over sub elements of list or dict."""
        if self._arg_data is None:
            return
        elif isinstance(self._arg_data, list):
            for idx, d in enumerate(self._arg_data):
                # not support to access parent from element args
                yield idx, AAZArgBrowser(self._arg_value[idx], d, parent=None)
        elif isinstance(self._arg_data, dict):
            for k, d in self._arg_data.items():
                # not support to access parent from element args
                yield k, AAZArgBrowser(self._arg_value[k], d, parent=None)
        else:
            raise NotImplementedError()

    @property
    def data(self):
        return self._arg_data

    @property
    def is_patch(self):
        return self._arg_value._is_patch    # pylint: disable=protected-access
