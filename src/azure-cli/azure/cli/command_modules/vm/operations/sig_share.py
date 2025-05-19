# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import register_command, AAZListArg, AAZStrArg
from azure.cli.core.azclierror import ArgumentUsageError
from ..aaz.latest.sig.share import Update as _SigShareUpdate
from ..aaz.latest.sig import Wait as _SigWait

logger = get_logger(__name__)


@register_command(
    "sig share add",
)
class SigShareAdd(_SigShareUpdate):
    """Share gallery with subscriptions and tenants.

    :example: Share entire gallery with all members of a subscription and/or tenant.
        az sig share add --resource-group MyResourceGroup --gallery-name MyGallery \\
        --subscription-ids subId1 subId2 --tenant-ids tenantId1 tenantId2
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.subscription_ids = AAZListArg(
            options=["--subscription-ids"],
            help="A list of subscription ids to share the gallery with.",
        )
        subscription_ids = args_schema.subscription_ids
        subscription_ids.Element = AAZStrArg()

        args_schema.tenant_ids = AAZListArg(
            options=["--tenant-ids"],
            help="A list of tenant ids to share the gallery with.",
        )
        tenant_ids = args_schema.tenant_ids
        tenant_ids.Element = AAZStrArg()

        args_schema.operation_type._required = False
        args_schema.operation_type._registered = False
        args_schema.groups._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if not args.subscription_ids and not args.tenant_ids:
            raise ArgumentUsageError('At least one of subscription ids or tenant ids must be provided.')

        args.operation_type = 'Add'
        args.groups = []
        if args.subscription_ids:
            args.groups.append({
                'type': 'Subscriptions',
                'ids': args.subscription_ids
            })
        if args.tenant_ids:
            args.groups.append({
                'type': 'AADTenants',
                'ids': args.tenant_ids
            })


@register_command(
    "sig share remove",
)
class SigShareRemove(_SigShareUpdate):
    """Stop sharing gallery with a subscription or tenant.

    :example: Stop sharing with a subscription or tenant ID
        az sig share remove --resource-group MyResourceGroup --gallery-name MyGallery \\
        --subscription-ids subId1 subId2 --tenant-ids tenantId1 tenantId2
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.subscription_ids = AAZListArg(
            options=["--subscription-ids"],
            help="A list of subscription ids to share the gallery with.",
        )
        subscription_ids = args_schema.subscription_ids
        subscription_ids.Element = AAZStrArg()

        args_schema.tenant_ids = AAZListArg(
            options=["--tenant-ids"],
            help="A list of tenant ids to share the gallery with.",
        )
        tenant_ids = args_schema.tenant_ids
        tenant_ids.Element = AAZStrArg()

        args_schema.operation_type._required = False
        args_schema.operation_type._registered = False
        args_schema.groups._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if not args.subscription_ids and not args.tenant_ids:
            raise ArgumentUsageError('At least one of subscription ids or tenant ids must be provided.')
        args.operation_type = 'Remove'
        args.groups = []
        if args.subscription_ids:
            args.groups.append({
                'type': 'Subscriptions',
                'ids': args.subscription_ids
            })
        if args.tenant_ids:
            args.groups.append({
                'type': 'AADTenants',
                'ids': args.tenant_ids
            })


@register_command(
    "sig share reset",
)
class SigShareReset(_SigShareUpdate):
    """Disable gallery from being shared with subscription or tenant.

    :example: Reset sharing profile of a gallery.
        az sig share reset --resource-group MyResourceGroup --gallery-name MyGallery
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.operation_type._required = False
        args_schema.operation_type._registered = False
        args_schema.groups._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.operation_type = 'Reset'
        args.groups = []


@register_command(
    "sig share enable-community"
)
class SigShareEnableCommunity(_SigShareUpdate):
    """Allow to share gallery to the community.

    :example: Allow to share gallery to the community
        az sig share enable-community --resource-group MyResourceGroup --gallery-name MyGallery
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.subscription_ids = AAZListArg(
            options=["--subscription-ids"],
            help="A list of subscription ids to share the gallery with.",
        )
        subscription_ids = args_schema.subscription_ids
        subscription_ids.Element = AAZStrArg()

        args_schema.tenant_ids = AAZListArg(
            options=["--tenant-ids"],
            help="A list of tenant ids to share the gallery with.",
        )
        tenant_ids = args_schema.tenant_ids
        tenant_ids.Element = AAZStrArg()

        args_schema.operation_type._required = False
        args_schema.operation_type._registered = False
        args_schema.groups._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.operation_type = 'EnableCommunity'
        args.groups = []
        if args.subscription_ids:
            args.groups.append({
                'type': 'Subscriptions',
                'ids': args.subscription_ids
            })
        if args.tenant_ids:
            args.groups.append({
                'type': 'AADTenants',
                'ids': args.tenant_ids
            })


@register_command(
    "sig share wait"
)
class SigShareWait(_SigWait):
    """Place the CLI in a waiting state until a condition of a shared gallery is met.

    :example: Place the CLI in a waiting state until the gallery sharing object is updated.
        az sig share wait --updated --resource-group MyResourceGroup --gallery-name Gallery
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.gallery_name._help['short-summary'] = 'Gallery name.'
        args_schema.expand._registered = False
        args_schema.select._registered = False

        return args_schema
