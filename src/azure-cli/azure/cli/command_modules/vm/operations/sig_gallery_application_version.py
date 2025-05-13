# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.sig.gallery_application.version import Create as _SigGalleryApplicationVersionCreate, Update as _SigGalleryApplicationVersionUpdate

logger = get_logger(__name__)


class SigGalleryApplicationVersionCreate(_SigGalleryApplicationVersionCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.install_command._required = True
        args_schema.package_file_link._required = True
        args_schema.remove_command._required = True
        return args_schema


class SiggalleryApplicationversionUpdate(_SigGalleryApplicationVersionUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.package_file_link._required = True
        return args_schema
