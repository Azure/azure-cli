# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType, get_sdk, supported_api_version


class MultiAPIAdaptor(object):
    # We will bridge all the code difference here caused by SDK breaking changes
    def __init__(self, cli_ctx):
        self.old_api = supported_api_version(cli_ctx, resource_type=ResourceType.MGMT_AUTHORIZATION,
                                             max_api='2015-07-01')
        self.cli_ctx = cli_ctx

    def _init_individual_permission(self, cfg):
        Permission = get_sdk(self.cli_ctx, ResourceType.MGMT_AUTHORIZATION, 'Permission', mod='models',
                             operation_group='role_definitions')
        permission = Permission(actions=cfg.get('actions', None),
                                not_actions=cfg.get('notActions', None))
        if not self.old_api:
            permission.data_actions = cfg.get('dataActions', None)
            permission.not_data_actions = cfg.get('notDataActions', None)
        return permission

    def _init_permissions(self, role_definition_input):
        # we will handle with or w/o 'permissions'
        if 'permissions' in role_definition_input:
            return [self._init_individual_permission(p) for p in role_definition_input['permissions']]
        return [self._init_individual_permission(role_definition_input)]

    def create_role_definition(self, client, role_name, role_id, role_definition_input):
        RoleDefinitionBase = get_sdk(self.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                     'RoleDefinitionProperties' if self.old_api else 'RoleDefinition',
                                     mod='models', operation_group='role_definitions')
        role_configuration = RoleDefinitionBase(role_name=role_name,
                                                description=role_definition_input.get('description', None),
                                                type='CustomRole',
                                                assignable_scopes=role_definition_input['assignableScopes'],
                                                permissions=self._init_permissions(role_definition_input))
        scope = role_definition_input['assignableScopes'][0]
        if self.old_api:
            return client.create_or_update(role_definition_id=role_id, scope=scope, properties=role_configuration)
        return client.create_or_update(role_definition_id=role_id, scope=scope, role_definition=role_configuration)

    def create_role_assignment(self, client, assignment_name, role_id, object_id, scope, assignee_principal_type=None):
        RoleAssignmentCreateParameters = get_sdk(
            self.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
            'RoleAssignmentProperties' if self.old_api else 'RoleAssignmentCreateParameters',
            mod='models', operation_group='role_assignments')
        parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=object_id)
        if assignee_principal_type:
            parameters.principal_type = assignee_principal_type
        return client.create(scope, assignment_name, parameters)

    def get_role_property(self, obj, property_name):
        if self.old_api:
            if isinstance(obj, dict):
                obj = obj['properties']
            else:
                obj = obj.properties
        if isinstance(obj, dict):
            return obj[property_name]
        return getattr(obj, property_name)

    def set_role_property(self, obj, property_name, property_value):
        if self.old_api:
            if isinstance(obj, dict):
                obj = obj['properties']
            else:
                obj = obj.properties
        if isinstance(obj, dict):
            obj[property_name] = property_value
        else:
            obj.property_name = property_value
