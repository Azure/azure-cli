# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType, get_sdk, supported_api_version


class MultiAPIAdaptor:
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
        RoleDefinitionBase = get_sdk(self.cli_ctx, ResourceType.MGMT_AUTHORIZATION, 'RoleDefinition',
                                     mod='models', operation_group='role_definitions')
        role_configuration = RoleDefinitionBase(role_name=role_name,
                                                description=role_definition_input.get('description', None),
                                                type='CustomRole',
                                                assignable_scopes=role_definition_input['assignableScopes'],
                                                permissions=self._init_permissions(role_definition_input))
        scope = role_definition_input['assignableScopes'][0]
        return client.create_or_update(role_definition_id=role_id, scope=scope, role_definition=role_configuration)

    def create_role_assignment(self, client, assignment_name, role_id, object_id, scope, assignee_principal_type=None,
                               description=None, condition=None, condition_version=None):
        RoleAssignmentCreateParameters = get_sdk(
            self.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
            'RoleAssignmentProperties' if self.old_api else 'RoleAssignmentCreateParameters',
            mod='models', operation_group='role_assignments')
        parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=object_id)
        if assignee_principal_type:
            parameters.principal_type = assignee_principal_type
        if description:
            parameters.description = description
        if condition:
            parameters.condition = condition
        if condition_version:
            parameters.condition_version = condition_version
        return client.create(scope, assignment_name, parameters)

    def get_role_property(self, obj, property_name):  # pylint: disable=no-self-use
        """Get property for RoleDefinition and RoleAssignment object."""
        # 2015-07-01          RoleDefinition: flattened, RoleAssignment: unflattened
        # 2018-01-01-preview  RoleDefinition: flattened
        # 2020-04-01-preview                             RoleAssignment: flattened
        # Get property_name from properties if the model is unflattened.
        if isinstance(obj, dict):
            if 'properties' in obj:
                obj = obj['properties']
            return obj[property_name]

        if hasattr(obj, 'properties'):
            obj = obj.properties
        return getattr(obj, property_name)

    def set_role_property(self, obj, property_name, property_value):  # pylint: disable=no-self-use
        """Set property for RoleDefinition and RoleAssignment object.
        Luckily this function is only called for an RoleAssignment `obj` returned by the service, and `properties`
         has been processed, either by being flattened or set. We can definitively know whether `obj` is flattened
         or not.
        There is NO use case where `obj` is provided by the user and `properties` has not been processed.
         In such case, we won't be able to decide if `obj` is flattened or not."""
        if isinstance(obj, dict):
            if 'properties' in obj:
                obj = obj['properties']
            obj[property_name] = property_value
        else:
            if hasattr(obj, 'properties'):
                obj = obj.properties
            obj.property_name = property_value
