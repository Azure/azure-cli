# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.cli.core.azclierror import UserFault

from ._base import has_value
from .exceptions import AAZUnknownFieldError


class AAZSelectors:

    def __init__(self):
        self._selectors = {}

    def __getattr__(self, key):
        if key not in self._selectors:
            raise AAZUnknownFieldError(self, key)
        return self._selectors[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self._selectors[key] = value


class AAZSelector:  # pylint: disable=too-few-public-methods

    def __init__(self, ctx, name):
        self.ctx = ctx
        setattr(ctx.selectors, name, self)


class AAZJsonSelector(AAZSelector):

    def _get(self):
        raise NotImplementedError()

    def _set(self, value):
        raise NotImplementedError()

    def get(self):
        try:
            return self._get()
        except StopIteration:
            raise UserFault("ResourceNotFoundError")

    def set(self, value):
        try:
            self._set(value)
        except StopIteration:
            raise UserFault("ResourceNotFoundError")

    def required(self):
        value = self.get()
        if not has_value(value):
            raise UserFault("ResourceNotFoundError")
        return value
