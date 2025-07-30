# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from knack.log import get_logger
from azure.mgmt.core.tools import (
    parse_resource_id,
)
from azure.cli.core import telemetry
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.azclierror import (
    CLIInternalError,
    InvalidArgumentValueError
)
from ._utils import (
    generate_random_string,
    run_cli_cmd,
    is_valid_resource_id
)
from ._resource_config import (
    RESOURCE,
    AUTH_TYPE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES,
    SUPPORTED_AUTH_TYPE
)


logger = get_logger(__name__)


# Configs to provision an addon, note that
#   1. 'create' property contains the commands to create a target resource
#   2. 'delete' property contains the commands to delete a target resource
#   3. 'params' property specifies the values of parameters in those commands
#   4. If a parameter appears in target resource id defined in TARGET_RESOURCES, it should be specified as the same
#      name in commands. E.g, for RESOURCE.Postgres, the resource id is '/subscriptions/{subscription}/resourceGroups/
#      {target_resource_group}/providers/Microsoft.DBforPostgreSQL/servers/{server}/databases/{database}', so the
#      parameter names we used in commands are `target_resource_group`, `server`, `database`.
AddonConfig = {
    RESOURCE.Postgres: {
        'create': [
            'az postgres server create -g "{target_resource_group}" -n "{server}" -l "{location}" -u "{user}" \
                -p "{password}"',
            'az postgres db create -g "{target_resource_group}" -s "{server}" -n {database}'
        ],
        'delete': [
            'az postgres server delete -g "{target_resource_group}" -n "{server}" --yes',
            'az postgres db delete -g "{target_resource_group}" -s "{server}" -n "{database}" --yes'
        ],
        'params': {
            'target_resource_group': '_retrive_source_rg',
            'location': '_retrive_source_loc',
            'server': generate_random_string(length=5, prefix='server-', lower_only=True),
            'user': generate_random_string(length=5, prefix='user_', lower_only=True),
            'password': generate_random_string(length=12, ensure_complexity=True),
            'database': generate_random_string(length=5, prefix='db_', lower_only=True)
        }
    },
    RESOURCE.KeyVault: {
        'create': ['az keyvault create -g "{target_resource_group}" -n "{vault}" -l "{location}"'],
        'delete': ['az keyvault delete -g "{target_resource_group}" -n "{vault}" --yes'],
        'params': {
            'target_resource_group': '_retrive_source_rg',
            'location': '_retrive_source_loc',
            'vault': generate_random_string(length=5, prefix='vault-')
        }
    },
    RESOURCE.StorageBlob: {
        'create': ['az storage account create -g "{target_resource_group}" -n "{account}" -l "{location}"'],
        'delete': ['az storage account delete -g "{target_resource_group}" -n "{account}" --yes'],
        'params': {
            'target_resource_group': '_retrive_source_rg',
            'location': '_retrive_source_loc',
            'account': generate_random_string(length=5, prefix='account', lower_only=True)
        }
    }
}


class AddonBase:

    def __init__(self, cmd, source_id):
        self._cmd = cmd
        self._source_id = source_id
        self._params = self._prepare_params()

    def provision(self):
        '''Create the target resource, and return the parameters for connection creation.
        '''
        target_type = self._get_target_type()
        creation_steps = AddonConfig.get(target_type).get('create')

        logger.warning('Start creating a new %s', target_type.value)
        for cnt, step in enumerate(creation_steps):
            # apply parmeters to format the command
            cmd = step.format(**self._params)
            try:
                run_cli_cmd(cmd)
            except CLIInternalError as err:
                logger.warning('Creation failed, start rolling back')
                self.rollback(cnt)
                raise CLIInternalError('Provision failed, please create the target resource manually '
                                       'and then create the connection. Error details: {}'.format(str(err)))

        target_id = self.get_target_id()
        logger.warning('Created, the resource id is: %s', target_id)

        auth_info = self.get_auth_info()
        logger.warning('The auth info used to create connection is: %s', str(auth_info))

        return target_id, auth_info

    def get_target_id(self):
        '''Get the resource id of the provisioned target resource.
        '''
        target_type = self._get_target_type()
        target_resource = TARGET_RESOURCES.get(target_type)
        return target_resource.format(**self._params)

    def get_auth_info(self):
        '''Get the auth info for the provisioned target resource
        '''
        source_type = self._get_source_type()
        target_type = self._get_target_type()
        default_auth_type = SUPPORTED_AUTH_TYPE.get(source_type).get(target_type)[0]

        if default_auth_type == AUTH_TYPE.SystemIdentity:
            return {'auth_type': 'systemAssignedIdentity'}

        # Override the method when default auth type is not system identity
        raise CLIInternalError('The method get_auth_info should be overridden '
                               'when default auth type is not system identity.')

    def rollback(self, cnt=None):
        '''Delete the created resources if creation fails
        :param cnt: Step in which the creation fails
        '''
        target_type = self._get_target_type()
        deletion_steps = AddonConfig.get(target_type).get('delete')
        logger.warning('Start deleting the %s', target_type.value)

        if cnt is None:
            cnt = len(deletion_steps)

        # deletion should be in reverse order
        for index in range(cnt - 1, -1, -1):
            # apply parameters to format the command
            cmd = deletion_steps[index].format(**self._params)
            try:
                run_cli_cmd(cmd)
            except CLIInternalError:
                logger.warning('Rollback failed, please manually check and delete the unintended resources '
                               'in resource group: %s. You may use this command: %s',
                               self._params.get('source_resource_group'), cmd)
                return
        logger.warning('Rollback succeeded, the created resources were successfully deleted')

    def _prepare_params(self):
        '''Prepare the parameters used in CLI command
        '''
        params = {'subscription': get_subscription_id(self._cmd.cli_ctx)}
        target_type = self._get_target_type()

        for arg, val in AddonConfig.get(target_type).get('params').items():
            func = getattr(self, val, None)
            if func:
                val = func()
            params[arg] = val

        return params

    def _retrive_source_rg(self):
        '''Retrieve the resource group name in source resource id
        '''
        if not is_valid_resource_id(self._source_id):
            e = InvalidArgumentValueError('The source resource id is invalid: {}'.format(self._source_id))
            telemetry.set_exception(e, "source-id-invalid")
            raise e

        segments = parse_resource_id(self._source_id)
        return segments.get('resource_group')

    def _retrive_source_loc(self):
        '''Retrieve the location of source resource group
        '''
        rg = self._retrive_source_rg()
        output = run_cli_cmd('az group show -n "{}" -o json'.format(rg))
        return output.get('location')

    def _get_source_type(self):
        '''Get source resource type
        '''
        from ._validators import get_resource_regex

        for _type, resource in SOURCE_RESOURCES.items():
            matched = re.match(get_resource_regex(resource), self._source_id)
            if matched:
                return _type
        e = InvalidArgumentValueError('The source resource id is invalid: {}'.format(self._source_id))
        telemetry.set_exception(e, "source-id-invalid")
        raise e

    def _get_target_type(self):
        '''Get target resource type
        '''
        from ._validators import get_target_resource_name
        return get_target_resource_name(self._cmd)


class AddonPostgres(AddonBase):
    def get_auth_info(self):
        return {
            'auth_type': 'secret',
            'name': self._params.get('user'),
            'secret': self._params.get('password')
        }


AddonFactory = {
    RESOURCE.Postgres: AddonPostgres,
    RESOURCE.StorageBlob: AddonBase,
    RESOURCE.KeyVault: AddonBase
}
