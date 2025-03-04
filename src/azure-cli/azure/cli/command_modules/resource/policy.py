from azure.cli.command_modules.resource.aaz.latest.policy.definition._create import Create
from azure.cli.command_modules.resource.aaz.latest.policy.definition._delete import Delete
from azure.cli.command_modules.resource.aaz.latest.policy.definition._list import List
from azure.cli.command_modules.resource.aaz.latest.policy.definition._show import Show
from azure.cli.command_modules.resource.aaz.latest.policy.definition._update import Update

class PolicyDefinitionsCreate(Create):
    pass

    # @classmethod
    # def _build_arguments_schema(cls, *args, **kwargs):
    #     from azure.cli.core.aaz import AAZResourceIdArgFormat

    #     args_schema = super()._build_arguments_schema(*args, **kwargs)
    #     # args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
    #     #     template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/applicationGateways/{gateway_name}/frontendIPConfigurations/{}"
    #     # )

    #     return args_schema

class PolicyDefinitionsDelete(Delete):
    pass

class PolicyDefinitionsList(List):
    pass

class PolicyDefinitionCreate(Create):

    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        if not has_value(self.ctx.args.scope) and has_value(self.ctx.args.subscription):
            self.ctx.args.scope = f"/subscriptions/{self.ctx.args.subscription}"

class PolicyDefinitionsShow(Show):
    # @classmethod
    # def _build_arguments_schema(cls, *args, **kwargs):
    #     from azure.cli.core.aaz import AAZResourceIdArgFormat

    #     args_schema = super()._build_arguments_schema(*args, **kwargs)
    #     # args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
    #     #     template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/applicationGateways/{gateway_name}/frontendIPConfigurations/{}"
    #     # )

    #     return args_schema

    class PolicyDefinitionsGetBuiltIn(Show.PolicyDefinitionsGet):

        def __init__(self, ctx):
            super().__init__(ctx)

        @property
        def url(self):
            return self.client.format_url(
                "/providers/Microsoft.Authorization/policyDefinitions/{policyDefinitionName}",
                **self.url_parameters
            )

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "policyDefinitionName", self.ctx.args.name,
                    required=True,
                )
            }
            return parameters

    def pre_operations(self):
        pass

    def _execute_operations(self):
        from azure.cli.core.aaz import has_value
        if has_value(self.ctx.args.name) and not has_value(self.ctx.args.management_group) and not 'subscription_id' in self.ctx.args._data:
            try:
                return self.PolicyDefinitionsGetBuiltIn(ctx=self.ctx)()
            except (Exception) as ex:
                pass

        return super()._execute_operations()

    def post_operations(self):
        pass

class PolicyDefinitionsUpdate(Update):
    pass
