# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.aaz import has_value
from ..aaz.latest.sig import Create as _SigCreate, Update as _SigUpdate, Show as _SigShow

logger = get_logger(__name__)


class SigCreate(_SigCreate):
    def pre_operations(self):
        args = self.ctx.args

        if args.permissions == 'Community':
            if not has_value(args.publisher_uri) or not has_value(args.publisher_contact) \
                    or not has_value(args.eula) or not has_value(args.public_name_prefix):
                raise RequiredArgumentMissingError('If you want to share to the community, '
                                                   'you need to fill in all the following parameters:'
                                                   ' --publisher-uri, --publisher-email, --eula, --public-name-prefix.')


class SigUpdate(_SigUpdate):
    def pre_operations(self):
        args = self.ctx.args

        if args.permissions == 'Community':
            if not has_value(args.publisher_uri) or not has_value(args.publisher_contact) \
                    or not has_value(args.eula) or not has_value(args.public_name_prefix):
                raise RequiredArgumentMissingError('If you want to share to the community, '
                                                   'you need to fill in all the following parameters:'
                                                   ' --publisher-uri, --publisher-email, --eula, --public-name-prefix.')


class SigShow(_SigShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.expand._registered = False

        args_schema.sharing_groups = AAZBoolArg(
            options=['--sharing-groups'],
            help='The expand query option to query shared gallery groups.',
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if args.sharing_groups:
            args.expand = 'sharingProfile/Groups'
