# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import (
    CLIInternalError,
    ResourceNotFoundError,
    ValidationError,
    RequiredArgumentMissingError,
    ArgumentUsageError
)
from azure.cli.command_modules.vm.azure_stack._actions import _get_latest_image_version
from ._util import import_aaz_by_profile

logger = get_logger(__name__)

_VMImage = import_aaz_by_profile("vm.image")


class VMImageShow(_VMImage.Show):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.disk_encryption_set_id._registered = False
        args_schema.data_access_auth_mode._registered = False
        args_schema.disk_access_id._registered = False
        args_schema.public_network_access._registered = False
        args_schema.accelerated_network._registered = False
        args_schema.architecture._registered = False

        args_schema.disk_access = AAZStrArg(
            options=["--disk-access"],
            help="Name or ID of the disk access resource for using private endpoints on disks.",
        )
        args_schema.disk_encryption_set = AAZStrArg(
            options=["--disk-encryption-set"],
            help="Name or ID of disk encryption set that is used to encrypt the disk."
        )

        return args_schema


def show_vm_image(cmd, urn=None, publisher=None, offer=None, sku=None, version=None, location=None, edge_zone=None):
    from azure.cli.core.commands.parameters import get_one_of_subscription_locations
    from azure.cli.core.azclierror import (MutuallyExclusiveArgumentError,
                                           InvalidArgumentValueError)

    location = location or get_one_of_subscription_locations(cmd.cli_ctx)
    error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
    if urn:
        if any([publisher, offer, sku, edge_zone, version]):
            recommendation = 'Try to use --urn publisher:offer:sku:version or' \
                             ' --urn publisher:offer:sku:edge_zone:version'
            raise MutuallyExclusiveArgumentError(error_msg, recommendation)
        items = urn.split(":")
        if len(items) != 4 and len(items) != 5:
            raise InvalidArgumentValueError(
                '--urn should be in the format of publisher:offer:sku:version or publisher:offer:sku:edge_zone:version')
        if len(items) == 5:
            publisher, offer, sku, edge_zone, version = urn.split(":")
        elif len(items) == 4:
            publisher, offer, sku, version = urn.split(":")
        if version.lower() == 'latest':
            version = _get_latest_image_version(cmd.cli_ctx, location, publisher, offer, sku)
    elif not publisher or not offer or not sku or not version:
        raise RequiredArgumentMissingError(error_msg)

    client = _compute_client_factory(cmd.cli_ctx)
    return client.virtual_machine_images.get(location=location, publisher_name=publisher,
                                                 offer=offer, skus=sku, version=version)
