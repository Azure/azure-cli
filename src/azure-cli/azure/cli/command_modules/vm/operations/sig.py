# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
import json
from knack.log import get_logger

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.aaz import has_value
from ..aaz.latest.sig import Create as _SigCreate, Update as _SigUpdate, Show as _SigShow
from ..aaz.latest.sig.identity import Remove as _SigIdentityRemove
from .._vm_utils import IdentityType

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


class SigIdentityRemove(_SigIdentityRemove):
    def _execute_operations(self):
        self.pre_operations()
        self.GalleriesGet(ctx=self.ctx)()
        yield self.GalleriesUpdate(ctx=self.ctx)()
        self.post_operations()

    class GalleriesUpdate(_SigIdentityRemove.GalleriesUpdate):
        def _format_content(self, content):
            if isinstance(content, str):
                content = json.loads(content)

            existing_id = self.ctx.vars.instance.identity.userAssignedIdentities.to_serialized_data()
            if not existing_id:
                return json.dumps(content)

            id_to_remove = self.ctx.args.mi_user_assigned.to_serialized_data()
            if id_to_remove == []:
                id_to_remove = existing_id
            elif not id_to_remove:
                return json.dumps(content)

            if not content.get('identity', {}).get('type') == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED.value \
                    or content.get('identity', {}).get('type') == IdentityType.USER_ASSIGNED.value:
                return json.dumps(content)

            id_to_retain = [id for id in existing_id if id not in id_to_remove]

            if not id_to_retain:
                if content.get('identity', {}).get('type') == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED.value:
                    content['identity']['type'] = IdentityType.SYSTEM_ASSIGNED.value
                elif content.get('identity', {}).get('type') == IdentityType.USER_ASSIGNED.value:
                    content['identity']['type'] = IdentityType.NONE.value
                content['identity'].pop('userAssignedIdentities', None)
                return json.dumps(content)

            if id_to_remove:
                for key in list(id_to_remove):
                    content['identity']['userAssignedIdentities'][key] = None

            return json.dumps(content)

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            request.data = self._format_content(request.data)
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200, 202]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait,
                    session,
                    self.on_200,
                    self.on_error,
                    lro_options={"final-state-via": "location"},
                    path_format_arguments=self.url_parameters,
                )

            return self.on_error(session.http_response)
