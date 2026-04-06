# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
import json
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.aaz import has_value
from ..aaz.latest.sig import Create as _SigCreate, Update as _SigUpdate, Show as _SigShow
from ..aaz.latest.sig.identity import Remove as _SigIdentityRemove, Show as _SigIdentityShow
from .._vm_utils import MSI_LOCAL_ID, IdentityType

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
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.mi_system_assigned._registered = False
        args_schema.mi_user_assigned._registered = False

        args_schema.identities = AAZListArg(
            help="Space-separated identities to remove. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID),
        )
        args_schema.identities.Element = AAZStrArg()

        return args_schema

    def pre_instance_update(self, instance):
        # Get existing identity in json
        existing_identity = instance.to_serialized_data()

        # If currently do not have any identity, return
        if not existing_identity:
            return

        identities_to_be_removed = self.ctx.args.identities.to_serialized_data()

        remove_system_assigned_identity = False

        # If user not specifying any identity, means it is to remove system assigned identity
        if not identities_to_be_removed or len(identities_to_be_removed) < 1:
            remove_system_assigned_identity = True

        # Assign system assigned identity as a variable, so identity can be formatted
        if identities_to_be_removed and MSI_LOCAL_ID in identities_to_be_removed:
            remove_system_assigned_identity = True
            identities_to_be_removed.remove(MSI_LOCAL_ID)

        # Collect existing user assigned identity
        existing_emsis = [x.lower() for x in (existing_identity.get('userAssignedIdentities', {})).keys()]
        existing_identity['userAssignedIdentities'] = {}

        # If user is removing identities
        if identities_to_be_removed and len(identities_to_be_removed) > 0:
            emsis_to_remove = [x.lower() for x in identities_to_be_removed]

            # Check for invalid identity to be removed
            non_existing = [emsis for emsis in emsis_to_remove if emsis not in existing_emsis]
            if non_existing:
                raise CLIError("'{}' are not associated with '{}'".format(
                    ','.join(non_existing), self.ctx.args.gallery_name))

            # Collect emsis to be retained
            emsis_to_retain = [emsis for emsis in existing_emsis if emsis not in emsis_to_remove]

            if len(emsis_to_retain) < 1:  # if all emsis are gone, we need to update the type
                if existing_identity['type'] == IdentityType.USER_ASSIGNED.value:
                    existing_identity['type'] = IdentityType.NONE.value
                    existing_identity.pop('userAssignedIdentities')
                elif existing_identity['type'] == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED.value:
                    existing_identity['type'] = IdentityType.SYSTEM_ASSIGNED.value

            # Set {'x_emsis': {}} to remove x emsis when parse to API
            for emsis in emsis_to_remove:
                existing_identity['userAssignedIdentities'][emsis] = {}

        # If user is removing system assigned identity
        if remove_system_assigned_identity:
            if existing_identity['type'] == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED.value \
                    or existing_identity['type'] == IdentityType.USER_ASSIGNED.value:
                existing_identity['type'] = IdentityType.USER_ASSIGNED.value
            else:
                existing_identity['type'] = IdentityType.NONE.value

        if existing_identity['type'] == IdentityType.NONE.value \
                or existing_identity['type'] == IdentityType.SYSTEM_ASSIGNED.value:
            existing_identity.pop('userAssignedIdentities', None)

        self.ctx.vars.instance.identity = existing_identity

    class SubresourceSelector(_SigIdentityRemove.SubresourceSelector):
        def required(self):
            return self._get()

    class GalleriesUpdate(_SigIdentityRemove.GalleriesUpdate):
        def _format_content(self, content):
            if isinstance(content, str):
                content = json.loads(content)

            if not content.get('identity'):
                content['identity'] = {
                    'userAssignedIdentities': None,
                    'type': IdentityType.NONE.value
                }
                return json.dumps(content)

            identities = content.get('identity', {}).get('userAssignedIdentities')
            if identities:
                if 'UserAssigned' in identities.keys():
                    identities.pop('UserAssigned')

                for key in list(identities.keys()):
                    identities[key] = None

            if not content.get('identity', {}).get('userAssignedIdentities', {}):
                content['identity']['userAssignedIdentities'] = None

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


class SigIdentityShow(_SigIdentityShow):
    def _output(self, *args, **kwargs):
        # This is to fix "When user is trying to run az sig show on sig that is not being assigned any identity,
        # it will raise ResourceNotFoundError" issue
        result = self.deserialize_output(self.ctx.selectors.subresource.get(), client_flatten=True)
        return result
