# `GraphClient` - Microsoft Graph API client

Azure CLI has been migrated to Microsoft Graph API for Azure Active Directory operations. A lightweight client `azure.cli.command_modules.role._msgrpah.GraphClient` is developed for calling Microsoft Graph API.

## Create a `GraphClient` instance

`GraphClient` should NEVER be instantiated directly, but always through the client factory `azure.cli.command_modules.role.graph_client_factory`.

```py
# Correct!
from azure.cli.command_modules.role import graph_client_factory
graph_client = graph_client_factory(cli_ctx)

# Wrong!
from azure.cli.command_modules.role._msgrpah import GraphClient
graph_client = GraphClient(cli_ctx)
```

## Request

The underlying Microsoft Graph API is exposed as `GraphClient` methods. For example, [Create application](https://docs.microsoft.com/en-us/graph/api/application-post-applications) API corresponds to `application_create`.

The order of the verb ("create") and the noun ("application") is inverted to keep alignment with Azure CLI commands like `az ad app create` and old Python SDK `azure-graphrbac` methods like `graph_client.applications.create`. This makes it easier to find a method/API from the new `GraphClient` and migrate to it:

```diff
- graph_client.applications.create(app_create_param)
+ graph_client.application_create(body)
```

The `body` argument for the request should be a `dict` object as defined by the underlying API. For example, [Create application](https://docs.microsoft.com/en-us/graph/api/application-post-applications) takes a `dict` object defined by [application resource type](https://docs.microsoft.com/en-us/graph/api/resources/application).

For example, to create an application with certain `displayName`:

```py
body = {"displayName": display_name}
app = graph_client.application_create(body)
```

## Response

Like `body`, the response is also a `dict` object, returned by the underlying API. The `dict` object is deserialized from the JSON response, **unchanged**, meaning any client-side manipulation defined by REST API spec (such as flattening) doesn't take place.

For example, to get an application's object ID:

```py
app_object_id = app['id']
```

## Error

All `GraphClient` methods raise an `azure.cli.command_modules.role.GraphError` exception if the underlying APIs return a status code >= 400.

Say we catch the exception as `ex`. `str(ex)` gives the `error.message` field of the response JSON. `ex.response` gives the raw response, as a `requests.models.Response` object.

For example, to retrieve the error message and status code:

```py
message = str(ex)
status_code = ex.response.status_code
```

## A full example

Here is a full example `graph_demo.py`. It does several tasks:

1. Create an application and a service principal for this application.
2. Resolve service principal's object ID from its service principal name.
3. Delete the application.

```py
from azure.cli.core import get_default_cli

from knack.log import get_logger

logger = get_logger(__name__)


def create_application_and_service_principal(cli_ctx, display_name):
    """Create an application with display_name. Then create a service principal for this application."""
    from azure.cli.command_modules.role import graph_client_factory, GraphError
    graph_client = graph_client_factory(cli_ctx)
    try:
        body = {"displayName": display_name}
        app = graph_client.application_create(body)
        sp = graph_client.service_principal_create({"appId": app['appId']})
        return app, sp
    except GraphError as ex:
        logger.exception(ex)


def delete_application(cli_ctx, object_id):
    """Delete an application specified by its object ID."""
    from azure.cli.command_modules.role import graph_client_factory, GraphError
    graph_client = graph_client_factory(cli_ctx)
    try:
        graph_client.application_delete(object_id)
    except GraphError as ex:
        logger.exception(ex)


def resolve_service_principal_id(cli_ctx, service_principal_name):
    """Resolve service principal's object ID from its service principal name."""
    from azure.cli.command_modules.role import graph_client_factory, GraphError
    graph_client = graph_client_factory(cli_ctx)
    try:
        service_principals = graph_client.service_principal_list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(service_principal_name))
        return service_principals[0]['id'] if service_principals else None
    except GraphError as ex:
        logger.exception(ex)


def main():
    cli_ctx = get_default_cli()

    app, sp = create_application_and_service_principal(cli_ctx, 'azure-cli-test')
    print('Created application {} and service principal {}'.format(app['id'], sp['id']))

    resolved_sp_object_id = resolve_service_principal_id(cli_ctx, sp['appId'])
    print('appId {} is resolved to service principal {}'.format(app['appId'], resolved_sp_object_id))

    delete_application(cli_ctx, app['id'])


if __name__ == "__main__":
    main()
```
