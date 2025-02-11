# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger
from ._util import import_aaz_by_profile

logger = get_logger(__name__)

_SigImageDefinition = import_aaz_by_profile("sig.image_definition")


class SigImageDefinitionUpdate(_SigImageDefinition.Update):
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
