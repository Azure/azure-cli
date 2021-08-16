The document provides instructions and guidelines on how to board param persist feature, prevoius name local context. The public feature name to end user is param persist. The usage is at [here](https://docs.microsoft.com/cli/azure/param-persist-howto). In implementation, it's referenced as local context. The 2 terms are equivalent in this doc.

## Local context attribute

Local context attribute is an abstraction of the definition for local context. We use this class to define how the argument supports local context.

There are 3 properties of local context attribute.

- **name**

`name` is the argument name used in local context. Usually we just use the name which defined in the function signature, for example, `resource_group_name`.

- **scopes**

`scopes` is an array of strings. It defines where this local context value can be referenced. The value could be a command group or a command, for example, `['vm', 'network']`. If one argument can be referenced in all the commands, you can define it as `['all']`. `scopes` is meaningful only when `SET` is in actions.
    
- **actions**

`actions` is an array of [`LocalContextAction`](#Local context action). It defines whether set the command parameter value to local context or get value from local context. We can define both `GET` and `SET` action for one argument.


## Local context action

Local context action is defined as an enum type. The available values are `GET` and `SET`.

- **GET**

Used for retrieving value from local context.

- **SET**

Used for saving value to local context.


## Parameters which support `all` scope by default

We define local context attribute for some command parameters by default. Commands whose function signature has the same argument name will support local context by default.

All these parameters are listed here:

- *resource_group_name*

```python
    local_context_attribute=LocalContextAttribute(
        name='resource_group_name',
        actions=[LocalContextAction.SET, LocalContextAction.GET],
        scopes=[ALL]
    ))
```

- *vnet_name*

```python
    local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.GET])
```

- *subnet*

```python
    local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.GET])
```

For example, below is function signature for `az network vnet create`:

```python
def create_vnet(cmd, resource_group_name, vnet_name, vnet_prefixes='10.0.0.0/16',
                subnet_name=None, subnet_prefix=None, dns_servers=None,
                location=None, tags=None, vm_protection=None, ddos_protection=None,
                ddos_protection_plan=None):
```

As `resource_group_name` is defined in the signature, it will automatically support local context.


## Suggestions

- Only enable local context feature for resource dependency parameters.
- Do not define `GET` action for `name` parameter in `create` and `delete` command.
- Define `SET` action only in `create` command.

## Examples

In order to create a webapp, a user needs to prepare an appservice plan first. Previously the user needed to run below commands to complete this scenario:

```azurecli
az group create --name myResourceGroup --location westus
az appservice plan create -g myResourceGroup --name myPlan
az webapp create -g myResourceGroup --plan myPlan --name myWebapp
```

The user has to input resource group name 3 times and plan name 2 times for this scenario. To reduce these duplicate type in, we need to enable local context feature for these parameters as below:

- `az group create`: *set resource group name*
> azure-cli/azure/cli/command_modules/resource/_params.py

```python
# define SET action for resource group name
with self.argument_context('group create') as c:
    c.argument('rg_name',
                local_context_attribute=LocalContextAttribute(name='resource_group_name',actions=[LocalContextAction.SET], scopes=[ALL]))
```

- `az appservice plan create`: *get resource group name & set plan name*

> azure-cli/azure/cli/command_modules/appservice/custom.py

```python
# get resource group name from local context by define function argument name as `resource_group_name`
def create_app_service_plan(cmd, resource_group_name, name, is_linux, hyper_v, per_site_scaling=False,
                            app_service_environment=None, sku='B1', number_of_workers=None, location=None,
                            tags=None, no_wait=False):
```

> azure-cli/azure/cli/command_modules/appservice/_params.py

```python
# define SET action for plan name
with self.argument_context('appservice plan create') as c:
    c.argument('name',
               local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.SET], scopes=['appservice', 'webapp', 'functionapp']))
```

- `az webapp create`: *get resource group name & get plan name & set webapp name*

> azure-cli/azure/cli/command_modules/appservice/custom.py

```python
# get resource group name from local context by define function argument name as `resource_group_name`
def create_webapp(cmd, resource_group_name, name, plan, runtime=None, startup_file=None,  # pylint: disable=too-many-statements,too-many-branches
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None, docker_registry_server_password=None, docker_registry_server_user=None,
                  multicontainer_config_type=None, multicontainer_config_file=None, tags=None,
                  using_webapp_up=False, language=None):
```

> azure-cli/azure/cli/command_modules/appservice/_params.py

```python
# define SET action for webapp name
# define GET action for plan name
with self.argument_context('webapp create') as c:
    c.argument('name',
                local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.SET], scopes=['webapp']))
    c.argument('plan',
                local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
```
