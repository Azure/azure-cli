# # --------------------------------------------------------------------------------------------
# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License. See License.txt in the project root for license information.
# # --------------------------------------------------------------------------------------------
# # pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
# from knack.log import get_logger
#
# from azure.cli.core.aaz import has_value
# from azure.cli.core.azclierror import (
#     InvalidArgumentValueError,
#     MutuallyExclusiveArgumentError,
#     RequiredArgumentMissingError,
# )
# from azure.cli.command_modules.vm.azure_stack._actions import _get_latest_image_version
# from ._util import import_aaz_by_profile
#
# logger = get_logger(__name__)
#
# _VMImage = import_aaz_by_profile("vm.image")
#
#
# class VMImageShow(_VMImage.Show):
#     @classmethod
#     def _build_arguments_schema(cls, *args, **kwargs):
#         from azure.cli.core.aaz import AAZStrArg
#         args_schema = super()._build_arguments_schema(*args, **kwargs)
#
#         args_schema.urn = AAZStrArg(
#             options=["--urn"],
#             help="URN, in format of 'publisher:offer:sku:version' or 'publisher:offer:sku:edge_zone:version'. If specified, other argument values can be omitted.",
#         )
#
#         return args_schema
#
#     def pre_operations(self):
#         args = self.ctx.args
#         error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
#
#         if has_value(args.urn):
#             if any([has_value(args.publisher), has_value(args.offer),
#                     has_value(args.sku), has_value(args.version)]):
#                 recommendation = 'Try to use --urn publisher:offer:sku:version or' \
#                                  ' --urn publisher:offer:sku:edge_zone:version'
#                 raise MutuallyExclusiveArgumentError(error_msg, recommendation)
#             items = args.urn.split(":")
#             if len(items) != 4 and len(items) != 5:
#                 raise InvalidArgumentValueError(
#                     '--urn should be in the format of publisher:offer:sku:version or publisher:offer:sku:edge_zone:version')
#             if len(items) == 5:
#                 args.publisher, args.offer, args.sku, args.edge_zone, args.version = args.urn.split(":")
#             elif len(items) == 4:
#                 args.publisher, args.offer, args.sku, args.version = args.urn.split(":")
#             if args.version.lower() == 'latest':
#                 args.version = _get_latest_image_version(self.cli_ctx, args.location, args.publisher, args.offer, args.sku)
#
#         elif (not has_value(args.publisher) or not has_value(args.offer)
#               or not has_value(args.sku) or not has_value(args.version)):
#             raise RequiredArgumentMissingError(error_msg)
