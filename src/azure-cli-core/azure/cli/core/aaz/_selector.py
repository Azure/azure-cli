# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from ._arg import has_value


class AAZSelector:

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
            self._get()
        except StopIteration:
            raise ResourceNotFoundError()

    def set(self, value):
        try:
            self._set(value)
        except StopIteration:
            raise ResourceNotFoundError()

    def required(self):
        value = self.get()
        if not has_value(value):
            raise ResourceNotFoundError()
