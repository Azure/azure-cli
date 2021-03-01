# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
logger = get_logger(__name__)


def process_args_with_built_in_alias(cli_ctx, args):
    # [] or ['az'] can just return
    if not args or (len(args) == 1 and args[0] == 'az'):
        return

    # Check core config
    transform_built_in_alias = cli_ctx.config.getboolean('core', 'transform_built_in_alias', fallback=True)
    if not transform_built_in_alias:
        return

    # process args
    from .alias_util import find_alias_and_transform_args
    if args[0] == 'az':
        args_transformed = ['az']
        args_transformed.extend(find_alias_and_transform_args(args[1:], None))
    else:
        args_transformed = find_alias_and_transform_args(args, None)

    if args_transformed != args:
        logger.warning('`%s` is alias of `%s`', ' '.join(args), ' '.join(args_transformed))
        args[:] = args_transformed
