# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["webapp config ssl upload"] = """
"type": |-
    command
"short-summary": |-
    Upload an SSL certificate to a web app.
"examples":
-   "name": |-
        Upload an SSL certificate to a web app.
    "text": |-
        az webapp config ssl upload --certificate-password <certificate-password> --query [0] --certificate-file <certificate-file> --resource-group MyResourceGroup --output json --name MyWebapp
"""

helps["webapp config hostname"] = """
"type": |-
    group
"short-summary": |-
    Configure hostnames for a web app.
"""

helps["webapp webjob continuous remove"] = """
"type": |-
    command
"short-summary": |-
    Delete a specific continuous webjob.
"""

helps["webapp identity assign"] = """
"type": |-
    command
"short-summary": |-
    assign or disable managed service identity to the webapp
"examples":
-   "name": |-
        Assign or disable managed service identity to the webapp.
    "text": |-
        az webapp identity assign --resource-group MyResourceGroup --name MyUniqueApp
"""

helps["webapp config hostname get-external-ip"] = """
"type": |-
    command
"short-summary": |-
    Get the external-facing IP address for a web app.
"""

helps["webapp show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a web app.
"examples":
-   "name": |-
        Get the details of a web app.
    "text": |-
        az webapp show --name MyWebapp --resource-group MyResourceGroup
"""

helps["webapp deployment container config"] = """
"type": |-
    command
"short-summary": |-
    Configure continuous deployment via containers.
"examples":
-   "name": |-
        Configure continuous deployment via containers.
    "text": |-
        az webapp deployment container config --enable-cd false --resource-group MyResourceGroup --name MyWebapp
"""

helps["functionapp deployment source sync"] = """
"type": |-
    command
"short-summary": |-
    Synchronize from the repository. Only needed under manual integration mode.
"examples":
-   "name": |-
        Synchronize from the repository. Only needed under manual integration mode.
    "text": |-
        az functionapp deployment source sync --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["functionapp delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a function app.
"examples":
-   "name": |-
        Delete a function app.
    "text": |-
        az functionapp delete --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["webapp config container set"] = """
"type": |-
    command
"short-summary": |-
    Set a web app container's settings.
"examples":
-   "name": |-
        Set a web app container's settings.
    "text": |-
        az webapp config container set --docker-registry-server-password <docker-registry-server-password> --docker-custom-image-name MyDockerCustomImage --resource-group MyResourceGroup --docker-registry-server-url <docker-registry-server-url> --name MyWebapp --docker-registry-server-user <docker-registry-server-user>
"""

helps["appservice plan update"] = """
"type": |-
    command
"short-summary": |-
    Update an app service plan.
"examples":
-   "name": |-
        Update an app service plan.
    "text": |-
        az appservice plan update --resource-group MyResourceGroup --sku B1 --name MyAppServicePlan
"""

helps["webapp traffic-routing clear"] = """
"type": |-
    command
"short-summary": |-
    Clear the routing rules and send all traffic to production.
"""

helps["webapp webjob"] = """
"type": |-
    group
"short-summary": |-
    Allows management operations for webjobs on a webapp.
"""

helps["webapp create"] = """
"type": |-
    command
"short-summary": |-
    Create a web app.
"long-summary": |-
    The web app's name must be able to produce a unique FQDN as AppName.azurewebsites.net.
"examples":
-   "name": |-
        Create a web app.
    "text": |-
        az webapp create --resource-group MyResourceGroup --plan MyPlan --name MyUniqueAppName
"""

helps["webapp"] = """
"type": |-
    group
"short-summary": |-
    Manage web apps.
"examples":
-   "name": |-
        Experimental command to create and deploy a web app. Current supports includes Node, Python on Linux & .NET Core, ASP.NET, staticHtml on Windows.
    "text": |-
        az webapp up --name MyWebapp
"""

helps["functionapp config ssl unbind"] = """
"type": |-
    command
"short-summary": |-
    Unbind an SSL certificate from a function app.
"""

helps["functionapp identity show"] = """
"type": |-
    command
"short-summary": |-
    display functionapp's managed service identity
"examples":
-   "name": |-
        Display functionapp's managed service identity.
    "text": |-
        az functionapp identity show --output json --resource-group MyResourceGroup --query [0] --name MyFunctionApp
"""

helps["webapp config appsettings"] = """
"type": |-
    group
"short-summary": |-
    Configure web app settings.
"""

helps["webapp log config"] = """
"type": |-
    command
"short-summary": |-
    Configure logging for a web app.
"examples":
-   "name": |-
        Configure logging for a web app.
    "text": |-
        az webapp log config --web-server-logging filesystem --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp config container"] = """
"type": |-
    group
"short-summary": |-
    Manage web app container settings.
"""

helps["webapp deployment source show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a source control deployment configuration.
"""

helps["webapp log show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a web app's logging configuration.
"""

helps["webapp config"] = """
"type": |-
    group
"short-summary": |-
    Configure a web app.
"""

helps["webapp config storage-account update"] = """
"type": |-
    command
"short-summary": |-
    Update an existing Azure storage account configuration on a web app. (Linux Web Apps and Windows Containers Web Apps Only)
"""

helps["functionapp cors show"] = """
"type": |-
    command
"short-summary": |-
    show allowed origins
"""

helps["webapp deployment slot create"] = """
"type": |-
    command
"short-summary": |-
    Create a deployment slot.
"examples":
-   "name": |-
        Create a deployment slot.
    "text": |-
        az webapp deployment slot create --slot <slot> --resource-group MyResourceGroup --name MyWebapp
"""

helps["functionapp cors"] = """
"type": |-
    group
"short-summary": |-
    Manage Cross-Origin Resource Sharing (CORS)
"""

helps["functionapp config hostname"] = """
"type": |-
    group
"short-summary": |-
    Configure hostnames for a function app.
"""

helps["appservice plan show"] = """
"type": |-
    command
"short-summary": |-
    Get the app service plans for a resource group or a set of resource groups.
"examples":
-   "name": |-
        Get the app service plans for a resource group or a set of resource groups.
    "text": |-
        az appservice plan show --output json --resource-group MyResourceGroup --name MyAppServicePlan
"""

helps["functionapp config ssl delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an SSL certificate from a function app.
"""

helps["functionapp config ssl bind"] = """
"type": |-
    command
"short-summary": |-
    Bind an SSL certificate to a function app.
"examples":
-   "name": |-
        Bind an SSL certificate to a function app.
    "text": |-
        az functionapp config ssl bind --ssl-type IP --resource-group MyResourceGroup --certificate-thumbprint <certificate-thumbprint> --name MyFunctionApp
"""

helps["functionapp config appsettings set"] = """
"type": |-
    command
"short-summary": |-
    Update a function app's settings.
"examples":
-   "name": |-
        Update a function app's settings.
    "text": |-
        az functionapp config appsettings set --settings <settings> --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["functionapp config appsettings list"] = """
"type": |-
    command
"short-summary": |-
    Show settings for a function app.
"examples":
-   "name": |-
        Show settings for a function app.
    "text": |-
        az functionapp config appsettings list --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp deployment source config-zip"] = """
"type": |-
    command
"short-summary": |-
    Perform deployment using the kudu zip push deployment for a webapp.
"long-summary": |
    By default Kudu assumes that zip deployments do not require any build-related actions like npm install or dotnet publish. This can be overridden by including a .deployment file in your zip file with the following content '[config] SCM_DO_BUILD_DURING_DEPLOYMENT = true', to enable Kudu detection logic and build script generation process. See https://github.com/projectkudu/kudu/wiki/Configurable-settings#enabledisable-build-actions-preview. Alternately the setting can be enabled using the az webapp config appsettings set command.
"""

helps["webapp deployment user"] = """
"type": |-
    group
"short-summary": |-
    Manage user credentials for deployment.
"""

helps["webapp deployment container"] = """
"type": |-
    group
"short-summary": |-
    Manage container-based continuous deployment.
"""

helps["functionapp deployment source config-local-git"] = """
"type": |-
    command
"short-summary": |-
    Get a URL for a git repository endpoint to clone and push to for function app deployment.
"""

helps["webapp identity"] = """
"type": |-
    group
"short-summary": |-
    manage webapp's managed service identity
"""

helps["webapp deployment source config-local-git"] = """
"type": |-
    command
"short-summary": |-
    Get a URL for a git repository endpoint to clone and push to for web app deployment.
"""

helps["webapp config set"] = """
"type": |-
    command
"short-summary": |-
    Set a web app's configuration.
"examples":
-   "name": |-
        Set a web app's configuration.
    "text": |-
        az webapp config set --always-on false --resource-group MyResourceGroup --name MyWebapp
"""

helps["functionapp cors add"] = """
"type": |-
    command
"short-summary": |-
    Add allowed origins
"examples":
-   "name": |-
        Add allowed origins.
    "text": |-
        az functionapp cors add --resource-group <myRG> --allowed-origins https://myapps.com --name <myAppName>
"""

helps["webapp browse"] = """
"type": |-
    command
"short-summary": |-
    Open a web app in a browser.
"""

helps["webapp deployment"] = """
"type": |-
    group
"short-summary": |-
    Manage web app deployments.
"""

helps["webapp webjob triggered run"] = """
"type": |-
    command
"short-summary": |-
    Run a specific triggered webjob hosted on a webapp.
"""

helps["webapp up"] = """
"type": |-
    command
"short-summary": |-
    (Preview) Create and deploy existing local code to the webapp, by running the command from the folder where the code is present. Supports running the command in preview mode using --dryrun parameter. Current supports includes Node, Python,.NET Core, ASP.NET, staticHtml. Node, Python apps are created as Linux apps. .Net Core, ASP.NET and static HTML apps are created as Windows apps. If command is run from an empty folder, an empty windows webapp is created.
"""

helps["webapp config connection-string set"] = """
"type": |-
    command
"short-summary": |-
    Update a web app's connection strings.
"""

helps["webapp deleted restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a deleted web app.
"long-summary": |-
    Restores the files and settings of a deleted web app to the specified web app.
"""

helps["webapp config ssl list"] = """
"type": |-
    command
"short-summary": |-
    List SSL certificates for a web app.
"""

helps["webapp deployment source"] = """
"type": |-
    group
"short-summary": |-
    Manage web app deployment via source control.
"""

helps["webapp start"] = """
"type": |-
    command
"short-summary": |-
    Start a web app.
"examples":
-   "name": |-
        Start a web app.
    "text": |-
        az webapp start --name MyWebapp --resource-group MyResourceGroup
"""

helps["webapp deployment list-publishing-profiles"] = """
"type": |-
    command
"short-summary": |-
    Get the details for available web app deployment profiles.
"""

helps["functionapp deployment user set"] = """
"type": |-
    command
"short-summary": |-
    Update deployment credentials.
"long-summary": |-
    All function and web apps in the subscription will be impacted since they share the same deployment credentials.
"""

helps["functionapp deployment list-publishing-profiles"] = """
"type": |-
    command
"short-summary": |-
    Get the details for available function app deployment profiles.
"""

helps["webapp deployment slot delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a deployment slot.
"""

helps["functionapp"] = """
"type": |-
    group
"short-summary": |-
    Manage function apps.
"""

helps["functionapp config ssl list"] = """
"type": |-
    command
"short-summary": |-
    List SSL certificates for a function app.
"""

helps["webapp config storage-account list"] = """
"type": |-
    command
"short-summary": |-
    Get a web app's Azure storage account configurations. (Linux Web Apps and Windows Containers Web Apps Only)
"""

helps["webapp config snapshot restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a web app snapshot.
"""

helps["webapp deployment slot auto-swap"] = """
"type": |-
    command
"short-summary": |-
    Configure deployment slot auto swap.
"""

helps["webapp config backup list"] = """
"type": |-
    command
"short-summary": |-
    List backups of a web app.
"""

helps["webapp deleted list"] = """
"type": |-
    command
"short-summary": |-
    List web apps that have been deleted.
"""

helps["webapp config ssl delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an SSL certificate from a web app.
"examples":
-   "name": |-
        Delete an SSL certificate from a web app.
    "text": |-
        az webapp config ssl delete --certificate-thumbprint <certificate-thumbprint> --resource-group MyResourceGroup
"""

helps["webapp config backup show"] = """
"type": |-
    command
"short-summary": |-
    Show the backup schedule for a web app.
"""

helps["webapp deployment source delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a source control deployment configuration.
"""

helps["webapp config storage-account delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a web app's Azure storage account configuration. (Linux Web Apps and Windows Containers Web Apps Only)
"""

helps["webapp config backup create"] = """
"type": |-
    command
"short-summary": |-
    Create a backup of a web app.
"""

helps["functionapp config hostname add"] = """
"type": |-
    command
"short-summary": |-
    Bind a hostname to a function app.
"""

helps["functionapp identity remove"] = """
"type": |-
    command
"short-summary": |-
    Disable functionapp's managed service identity
"""

helps["functionapp create"] = """
"type": |-
    command
"short-summary": |-
    Create a function app.
"long-summary": |-
    The function app's name must be able to produce a unique FQDN as AppName.azurewebsites.net.
"examples":
-   "name": |-
        Create a function app.
    "text": |-
        az functionapp create --consumption-plan-location <consumption-plan-location> --storage-account MyStorageAccount --resource-group MyResourceGroup  --name MyUniqueAppName
"""

helps["webapp cors"] = """
"type": |-
    group
"short-summary": |-
    Manage Cross-Origin Resource Sharing (CORS)
"""

helps["webapp deployment slot list"] = """
"type": |-
    command
"short-summary": |-
    List all deployment slots.
"examples":
-   "name": |-
        List all deployment slots.
    "text": |-
        az webapp deployment slot list --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp config connection-string list"] = """
"type": |-
    command
"short-summary": |-
    Get a web app's connection strings.
"""

helps["webapp auth update"] = """
"type": |-
    command
"short-summary": |-
    Update the authentication settings for the webapp.
"""

helps["webapp stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a web app.
"examples":
-   "name": |-
        Stop a web app.
    "text": |-
        az webapp stop --name MyWebapp --resource-group MyResourceGroup
"""

helps["webapp config backup"] = """
"type": |-
    group
"short-summary": |-
    Manage backups for web apps.
"""

helps["webapp delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a web app.
"examples":
-   "name": |-
        Delete a web app.
    "text": |-
        az webapp delete --resource-group MyResourceGroup --name MyWebapp
"""

helps["functionapp config ssl"] = """
"type": |-
    group
"short-summary": |-
    Configure SSL certificates.
"""

helps["appservice plan delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an app service plan.
"""

helps["webapp log download"] = """
"type": |-
    command
"short-summary": |-
    Download a web app's log history as a zip file.
"long-summary": |-
    This command may not work with web apps running on Linux.
"examples":
-   "name": |-
        Download a web app's log history as a zip file.
    "text": |-
        az webapp log download --slot <slot> --resource-group MyResourceGroup --log-file <log-file> --name MyWebapp
"""

helps["webapp webjob triggered remove"] = """
"type": |-
    command
"short-summary": |-
    Delete a specific triggered webjob hosted on a webapp.
"""

helps["webapp webjob triggered log"] = """
"type": |-
    command
"short-summary": |-
    Get history of a specific triggered webjob hosted on a webapp.
"""

helps["webapp config hostname delete"] = """
"type": |-
    command
"short-summary": |-
    Unbind a hostname from a web app.
"""

helps["webapp webjob continuous list"] = """
"type": |-
    command
"short-summary": |-
    List all continuous webjobs on a selected webapp.
"examples":
-   "name": |-
        List all continuous webjobs on a selected webapp.
    "text": |-
        az webapp webjob continuous list --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp auth"] = """
"type": |-
    group
"short-summary": |-
    Manage webapp authentication and authorization
"""

helps["webapp config show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a web app's configuration.
"examples":
-   "name": |-
        Get the details of a web app's configuration.
    "text": |-
        az webapp config show --output json --name MyWebapp --query [0] --resource-group MyResourceGroup
"""

helps["webapp deployment container show-cd-url"] = """
"type": |-
    command
"short-summary": |-
    Get the URL which can be used to configure webhooks for continuous deployment.
"""

helps["functionapp deployment user"] = """
"type": |-
    group
"short-summary": |-
    Manage user credentials for deployment.
"""

helps["webapp list"] = """
"type": |-
    command
"short-summary": |-
    List web apps.
"""

helps["webapp config connection-string delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a web app's connection strings.
"""

helps["appservice plan"] = """
"type": |-
    group
"short-summary": |-
    Manage app service plans.
"""

helps["webapp config storage-account"] = """
"type": |-
    group
"short-summary": |-
    Manage a web app's Azure storage account configurations. (Linux Web Apps and Windows Containers Web Apps Only)
"""

helps["functionapp config ssl upload"] = """
"type": |-
    command
"short-summary": |-
    Upload an SSL certificate to a function app.
"examples":
-   "name": |-
        Upload an SSL certificate to a function app.
    "text": |-
        az functionapp config ssl upload --certificate-password <certificate-password> --query [0] --certificate-file <certificate-file> --resource-group MyResourceGroup --output json --name MyFunctionApp
"""

helps["webapp webjob triggered"] = """
"type": |-
    group
"short-summary": |-
    Allows management operations of triggered webjobs on a webapp.
"""

helps["functionapp list"] = """
"type": |-
    command
"short-summary": |-
    List function apps.
"examples":
-   "name": |-
        List function apps.
    "text": |-
        az functionapp list --output json
"""

helps["webapp webjob triggered list"] = """
"type": |-
    command
"short-summary": |-
    List all triggered webjobs hosted on a webapp.
"""

helps["webapp deployment source config"] = """
"type": |-
    command
"short-summary": |-
    Manage deployment from git or Mercurial repositories.
"examples":
-   "name": |-
        Perform deployment using the kudu zip push deployment for a webapp.
    "text": |-
        az webapp deployment source config-zip --src <src> --name MyWebapp --resource-group MyResourceGroup
-   "name": |-
        Get a URL for a git repository endpoint to clone and push to for web app deployment.
    "text": |-
        az webapp deployment source config-local-git --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp auth show"] = """
"type": |-
    command
"short-summary": |-
    Show the authentification settings for the webapp.
"""

helps["functionapp deployment source delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a source control deployment configuration.
"""

helps["appservice plan list"] = """
"type": |-
    command
"short-summary": |-
    List app service plans.
"examples":
-   "name": |-
        List app service plans.
    "text": |-
        az appservice plan list --resource-group MyResourceGroup
"""

helps["webapp cors show"] = """
"type": |-
    command
"short-summary": |-
    show allowed origins
"""

helps["functionapp config appsettings"] = """
"type": |-
    group
"short-summary": |-
    Configure function app settings.
"""

helps["webapp deployment user set"] = """
"type": |-
    command
"short-summary": |-
    Update deployment credentials.
"long-summary": |-
    All function and web apps in the subscription will be impacted since they share the same deployment credentials.
"examples":
-   "name": |-
        Update deployment credentials.
    "text": |-
        az webapp deployment user set --user-name MyUserName --password <password>
"""

helps["functionapp stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a function app.
"examples":
-   "name": |-
        Stop a function app.
    "text": |-
        az functionapp stop --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["functionapp show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a function app.
"examples":
-   "name": |-
        Get the details of a function app.
    "text": |-
        az functionapp show --name MyFunctionApp --resource-group MyResourceGroup
"""

helps["functionapp restart"] = """
"type": |-
    command
"short-summary": |-
    Restart a function app.
"examples":
-   "name": |-
        Restart a function app.
    "text": |-
        az functionapp restart --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["webapp config hostname list"] = """
"type": |-
    command
"short-summary": |-
    List all hostname bindings for a web app.
"examples":
-   "name": |-
        List all hostname bindings for a web app.
    "text": |-
        az webapp config hostname list --webapp-name MyWebapp --resource-group MyResourceGroup
"""

helps["appservice"] = """
"type": |-
    group
"short-summary": |-
    Manage App Service plans.
"""

helps["webapp config container show"] = """
"type": |-
    command
"short-summary": |-
    Get details of a web app container's settings.
"""

helps["webapp log tail"] = """
"type": |-
    command
"short-summary": |-
    Start live log tracing for a web app.
"long-summary": |-
    This command may not work with web apps running on Linux.
"examples":
-   "name": |-
        Start live log tracing for a web app.
    "text": |-
        az webapp log tail --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp config appsettings list"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a web app's settings.
"examples":
-   "name": |-
        Get the details of a web app's settings.
    "text": |-
        az webapp config appsettings list --name MyWebapp --resource-group MyResourceGroup
"""

helps["webapp cors add"] = """
"type": |-
    command
"short-summary": |-
    Add allowed origins
"examples":
-   "name": |-
        Add allowed origins.
    "text": |-
        az webapp cors add --name <myAppName> --allowed-origins https://myapps.com --resource-group <myRG>
"""

helps["webapp webjob continuous stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a specific continuous webjob.
"""

helps["webapp webjob continuous"] = """
"type": |-
    group
"short-summary": |-
    Allows management operations of continuous webjobs on a webapp.
"""

helps["webapp log"] = """
"type": |-
    group
"short-summary": |-
    Manage web app logs.
"""

helps["webapp config ssl bind"] = """
"type": |-
    command
"short-summary": |-
    Bind an SSL certificate to a web app.
"examples":
-   "name": |-
        Bind an SSL certificate to a web app.
    "text": |-
        az webapp config ssl bind --ssl-type IP --resource-group MyResourceGroup --certificate-thumbprint <certificate-thumbprint> --name MyWebapp
"""

helps["functionapp config show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a web app's configuration.
"""

helps["webapp config hostname add"] = """
"type": |-
    command
"short-summary": |-
    Bind a hostname to a web app.
"examples":
-   "name": |-
        Bind a hostname to a web app.
    "text": |-
        az webapp config hostname add --webapp-name MyWebapp --hostname <hostname> --resource-group MyResourceGroup
"""

helps["functionapp config hostname delete"] = """
"type": |-
    command
"short-summary": |-
    Unbind a hostname from a function app.
"""

helps["appservice plan create"] = """
"type": |-
    command
"short-summary": |-
    Create an app service plan.
"examples":
-   "name": |-
        Create an app service plan.
    "text": |-
        az appservice plan create --name MyPlan --sku B1 --resource-group MyResourceGroup
"""

helps["webapp config snapshot"] = """
"type": |-
    group
"short-summary": |-
    Manage web app snapshots.
"""

helps["webapp deleted"] = """
"type": |-
    group
"short-summary": |-
    Manage deleted web apps.
"""

helps["webapp traffic-routing"] = """
"type": |-
    group
"short-summary": |-
    Manage traffic routing for web apps.
"""

helps["functionapp config appsettings delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a function app's settings.
"""

helps["functionapp list-consumption-locations"] = """
"type": |-
    command
"short-summary": |-
    List available locations for running function apps.
"""

helps["functionapp identity assign"] = """
"type": |-
    command
"short-summary": |-
    assign or disable managed service identity to the functionapp
"""

helps["webapp config appsettings delete"] = """
"type": |-
    command
"short-summary": |-
    Delete web app settings.
"examples":
-   "name": |-
        Delete web app settings.
    "text": |-
        az webapp config appsettings delete --name MyWebapp --setting-names <setting-names> --resource-group MyResourceGroup
"""

helps["webapp config connection-string"] = """
"type": |-
    group
"short-summary": |-
    Manage a web app's connection strings.
"""

helps["functionapp start"] = """
"type": |-
    command
"short-summary": |-
    Start a function app.
"examples":
-   "name": |-
        Start a function app.
    "text": |-
        az functionapp start --resource-group MyResourceGroup --name MyFunctionApp
"""

helps["functionapp config hostname list"] = """
"type": |-
    command
"short-summary": |-
    List all hostname bindings for a function app.
"""

helps["webapp deployment slot swap"] = """
"type": |-
    command
"short-summary": |-
    Change deployment slots for a web app.
"examples":
-   "name": |-
        Change deployment slots for a web app.
    "text": |-
        az webapp deployment slot swap --target-slot <target-slot> --slot <slot> --name MyWebapp --resource-group MyResourceGroup
"""

helps["webapp restart"] = """
"type": |-
    command
"short-summary": |-
    Restart a web app.
"examples":
-   "name": |-
        Restart a web app.
    "text": |-
        az webapp restart --resource-group MyResourceGroup --name MyWebapp
"""

helps["webapp config backup update"] = """
"type": |-
    command
"short-summary": |-
    Configure a new backup schedule for a web app.
"""

helps["webapp list-runtimes"] = """
"type": |-
    command
"short-summary": |-
    List available built-in stacks which can be used for web apps.
"""

helps["webapp identity show"] = """
"type": |-
    command
"short-summary": |-
    display webapp's managed service identity
"examples":
-   "name": |-
        Display webapp's managed service identity.
    "text": |-
        az webapp identity show --output json --name MyWebapp --query [0] --resource-group MyResourceGroup
"""

helps["webapp config snapshot list"] = """
"type": |-
    command
"short-summary": |-
    List the restorable snapshots for a web app.
"""

helps["functionapp cors remove"] = """
"type": |-
    command
"short-summary": |-
    Remove allowed origins
"examples":
-   "name": |-
        Remove allowed origins.
    "text": |-
        az functionapp cors remove --resource-group <myRG> --allowed-origins https://myapps.com --name <myAppName>
"""

helps["webapp config storage-account add"] = """
"type": |-
    command
"short-summary": |-
    Add an Azure storage account configuration to a web app. (Linux Web Apps and Windows Containers Web Apps Only)
"""

helps["webapp webjob continuous start"] = """
"type": |-
    command
"short-summary": |-
    Start a specific continuous webjob on a selected webapp.
"""

helps["webapp config appsettings set"] = """
"type": |-
    command
"short-summary": |-
    Set a web app's settings.
"examples":
-   "name": |-
        Set a web app's settings.
    "text": |-
        az webapp config appsettings set --settings WEBSITE_NODE_DEFAULT_VERSION=6.9.1 --name MyUniqueApp --resource-group MyResourceGroup
"""

helps["webapp cors remove"] = """
"type": |-
    command
"short-summary": |-
    Remove allowed origins
"examples":
-   "name": |-
        Remove allowed origins.
    "text": |-
        az webapp cors remove --name <myAppName> --allowed-origins https://myapps.com --resource-group <myRG>
"""

helps["webapp traffic-routing set"] = """
"type": |-
    command
"short-summary": |-
    Configure routing traffic to deployment slots.
"""

helps["functionapp update"] = """
"type": |-
    command
"short-summary": |-
    Update a function app.
"""

helps["functionapp deployment source"] = """
"type": |-
    group
"short-summary": |-
    Manage function app deployment via source control.
"""

helps["webapp config backup restore"] = """
"type": |-
    command
"short-summary": |-
    Restore a web app from a backup.
"""

helps["webapp update"] = """
"type": |-
    command
"short-summary": |-
    Update a web app.
"examples":
-   "name": |-
        Update a web app.
    "text": |-
        az webapp update --https-only false --name MyAppName --resource-group MyResourceGroup
"""

helps["appservice list-locations"] = """
"type": |-
    command
"short-summary": |-
    List regions where a plan sku is available.
"""

helps["webapp identity remove"] = """
"type": |-
    command
"short-summary": |-
    Disable webapp's managed service identity
"""

helps["webapp config ssl unbind"] = """
"type": |-
    command
"short-summary": |-
    Unbind an SSL certificate from a web app.
"""

helps["functionapp config set"] = """
"type": |-
    command
"short-summary": |-
    Set the web app's configuration.
"""

helps["functionapp config hostname get-external-ip"] = """
"type": |-
    command
"short-summary": |-
    Get the external-facing IP address for a function app.
"""

helps["functionapp deployment source config"] = """
"type": |-
    command
"short-summary": |-
    Manage deployment from git or Mercurial repositories.
"examples":
-   "name": |-
        Perform deployment using the kudu zip push deployment for a function app.
    "text": |-
        az functionapp deployment source config-zip --src <src> --name MyFunctionApp --resource-group MyResourceGroup
"""

helps["functionapp identity"] = """
"type": |-
    group
"short-summary": |-
    manage functionapp's managed service identity
"""

helps["functionapp deployment source config-zip"] = """
"type": |-
    command
"short-summary": |-
    Perform deployment using the kudu zip push deployment for a function app.
"long-summary": |
    By default Kudu assumes that zip deployments do not require any build-related actions like npm install or dotnet publish. This can be overridden by including an .deployment file in your zip file with the following content '[config] SCM_DO_BUILD_DURING_DEPLOYMENT = true', to enable Kudu detection logic and build script generation process. See https://github.com/projectkudu/kudu/wiki/Configurable-settings#enabledisable-build-actions-preview. Alternately the setting can be enabled using the az functionapp config appsettings set command.
"""

helps["functionapp deployment source show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a source control deployment configuration.
"""

helps["webapp config ssl"] = """
"type": |-
    group
"short-summary": |-
    Configure SSL certificates for web apps.
"""

helps["webapp deployment slot"] = """
"type": |-
    group
"short-summary": |-
    Manage web app deployment slots.
"""

helps["webapp deployment source sync"] = """
"type": |-
    command
"short-summary": |-
    Synchronize from the repository. Only needed under manual integration mode.
"""

helps["functionapp deployment"] = """
"type": |-
    group
"short-summary": |-
    Manage function app deployments.
"""

helps["functionapp config"] = """
"type": |-
    group
"short-summary": |-
    Configure a function app.
"""

helps["webapp config container delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a web app container's settings.
"""

helps["webapp traffic-routing show"] = """
"type": |-
    command
"short-summary": |-
    Display the current distribution of traffic across slots.
"""

