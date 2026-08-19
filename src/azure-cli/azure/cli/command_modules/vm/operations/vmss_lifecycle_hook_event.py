# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access, too-few-public-methods
from ..aaz.latest.vmss.lifecycle_hook_event import Update as _VMSSLifecycleHookEventUpdate


class VMSSLifecycleHookEventUpdate(_VMSSLifecycleHookEventUpdate):
    """
    The PATCH lifecycleHookEvents API returns a 202, but the generated command only
    handles 200 and therefore fails with "Operation returned an invalid status ''".
    Poll the LRO to completion instead.
    """

    def _handler(self, command_args):
        super(_VMSSLifecycleHookEventUpdate, self)._handler(command_args)
        return self.build_lro_poller(self._execute_operations, self._output)

    def _execute_operations(self):
        self.pre_operations()
        yield self.VirtualMachineScaleSetLifeCycleHookEventsUpdate(ctx=self.ctx)()
        self.post_operations()

    class VirtualMachineScaleSetLifeCycleHookEventsUpdate(
            _VMSSLifecycleHookEventUpdate.VirtualMachineScaleSetLifeCycleHookEventsUpdate):

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200, 202]:
                return self.client.build_lro_polling(
                    False,
                    session,
                    self.on_200,
                    self.on_error,
                    lro_options={"final-state-via": "azure-async-operation"},
                    path_format_arguments=self.url_parameters,
                )

            return self.on_error(session.http_response)
