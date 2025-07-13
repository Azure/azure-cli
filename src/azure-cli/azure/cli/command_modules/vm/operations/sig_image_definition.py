# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.sig.image_definition import (Update as _SigImageDefinitionUpdate,
                                               ListShared as _SigImageDefinitionListShared)

logger = get_logger(__name__)


class SigImageDefinitionUpdate(_SigImageDefinitionUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.location._registered = False
        args_schema.tags._registered = False
        args_schema.architecture._registered = False
        args_schema.description._registered = False
        args_schema.disallowed._registered = False
        args_schema.end_of_life_date._registered = False
        args_schema.eula._registered = False
        args_schema.features._registered = False
        args_schema.hyper_v_generation._registered = False
        args_schema.identifier._registered = False
        args_schema.os_state._registered = False
        args_schema.os_type._registered = False
        args_schema.privacy_statement_uri._registered = False
        args_schema.purchase_plan._registered = False
        args_schema.recommended._registered = False
        args_schema.release_note_uri._registered = False

        return args_schema


class SigImageDefinitionListShared(_SigImageDefinitionListShared):
    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        if has_value(args.shared_to) and args.shared_to == 'subscription':
            args.shared_to = None
