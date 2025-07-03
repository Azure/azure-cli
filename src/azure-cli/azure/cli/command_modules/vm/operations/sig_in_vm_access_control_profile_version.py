# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument, too-many-branches
from knack.log import get_logger

from azure.cli.core.aaz import AAZListArg, AAZStrArg, register_command
from ..aaz.latest.sig.in_vm_access_control_profile_version import (Create as _SigInVMAccessControlProfileVersionCreate,
                                                                   Update as _SigInVMAccessControlProfileVersionUpdate)

logger = get_logger(__name__)


@register_command(
    "sig in-vm-access-control-profile-version create",
)
class SigInVMAccessControlProfileVersionCreate(_SigInVMAccessControlProfileVersionCreate):
    """Create a gallery in VM access control profile version.

    :example: Create or update a Gallery in VM access control profile version.
        az sig in-vm-access-control-profile-version create --resource-group myResourceGroup --gallery-name myGalleryName --profile-name myInVMAccessControlProfileName --profile-version 1.0.0 --location WestUS
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.default_access._required = True
        args_schema.mode._required = True
        args_schema.target_locations._registered = False

        args_schema.target_regions = AAZListArg(
            options=["--target-regions"],
            help="The target regions where the Resource Profile version is going to be replicated to.",
        )
        target_regions = args_schema.target_regions
        target_regions.Element = AAZStrArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if args.target_regions:
            args.target_locations = []
            for name in args.target_regions:
                args.target_locations.append({
                    'name': name
                })


@register_command(
    "sig in-vm-access-control-profile-version update",
)
class SigInVMAccessControlProfileVersionUpdate(_SigInVMAccessControlProfileVersionUpdate):
    """Update a gallery in VM access control profile version.

    :example: Update a Gallery in VM access control profile version.
        az sig in-vm-access-control-profile-version update --resource-group myResourceGroup --gallery-name myGalleryName --profile-name myInVMAccessControlProfileName --profile-version 1.0.0 --exclude-from-latest true
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.rules._registered = False
        args_schema.target_locations._registered = False

        args_schema.target_regions = AAZListArg(
            options=["--target-regions"],
            help="The target regions where the Resource Profile version is going to be replicated to.",
        )
        target_regions = args_schema.target_regions
        target_regions.Element = AAZStrArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if args.target_regions:
            args.target_locations = []
            for name in args.target_regions:
                args.target_locations.append({
                    'name': name
                })
