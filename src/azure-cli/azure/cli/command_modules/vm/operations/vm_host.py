# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.vm.host import Update as _VMHostUpdate

logger = get_logger(__name__)


class VMHostUpdate(_VMHostUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.host_group_name._options = ['--host-group']
        args_schema.host_name._options = ['-n', '--name']

        args_schema.location._registered = False
        args_schema.sku._registered = False
        args_schema.tags._registered = False
        args_schema.auto_replace_on_failure._registered = False
        args_schema.license_type._registered = False
        args_schema.platform_fault_domain._registered = False

        return args_schema
