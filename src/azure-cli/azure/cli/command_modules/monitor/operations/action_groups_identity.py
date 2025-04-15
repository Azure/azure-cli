# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access
from ..aaz.latest.monitor.action_group.identity import Assign as _AGIdentityAssign, \
    Remove as _AGIdentityRemove, Show as _AGIdentityShow


class AGIdentityAssign(_AGIdentityAssign):
    def _execute_operations(self):
        self.pre_operations()
        self.ActionGroupsGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.selectors.subresource.get())
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.post_instance_update(self.ctx.selectors.subresource.get())
        self.ActionGroupsCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.selectors.subresource.get(), client_flatten=True)
        return result

    class InstanceUpdateByJson(_AGIdentityAssign.InstanceUpdateByJson):
        def __call__(self, *args, **kwargs):
            self._update_instance(self.ctx.selectors.subresource.get())


class AGIdentityRemove(_AGIdentityRemove):
    def _execute_operations(self):
        self.pre_operations()
        self.ActionGroupsGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.selectors.subresource.get())
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.post_instance_update(self.ctx.selectors.subresource.get())
        self.ActionGroupsCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.selectors.subresource.get(), client_flatten=True)
        return result

    class InstanceUpdateByJson(_AGIdentityRemove.InstanceUpdateByJson):
        def __call__(self, *args, **kwargs):
            self._update_instance(self.ctx.selectors.subresource.get())


class AGIdentityShow(_AGIdentityShow):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.selectors.subresource.get(), client_flatten=True)
        return result
