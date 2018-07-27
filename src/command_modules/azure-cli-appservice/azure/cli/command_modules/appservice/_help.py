# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['appservice'] = """
type: group
short-summary: Manage App Service plans.
"""

helps['webapp'] = """
type: group
short-summary: Manage web apps.
"""

helps['webapp auth'] = """
    type: group
    short-summary: Manage webapp authentication and authorization
"""

helps['webapp auth show'] = """
    type: command
    short-summary: Show the authentification settings for the webapp.
"""

helps['webapp auth update'] = """
    type: command
    short-summary: Update the authentication settings for the webapp.
    examples:
    - name: Enable AAD by enabling authentication and setting AAD-associated parameters. Default provider is set to AAD. Must have created a AAD service principal beforehand.
      text: >
        az webapp auth update  -g myResourceGroup -n myUniqueApp --enabled true \\
          --action LoginWithAzureActiveDirectory \\
          --aad-allowed-token-audiences https://webapp_name.azurewebsites.net/.auth/login/aad/callback \\
          --aad-client-id ecbacb08-df8b-450d-82b3-3fced03f2b27 --aad-client-secret very_secret_password \\
          --aad-token-issuer-url https://sts.windows.net/54826b22-38d6-4fb2-bad9-b7983a3e9c5a/
    - name: Allow Facebook authentication by setting FB-associated parameters and turning on public-profile and email scopes; allow anonymous users
      text: >
        az webapp auth update -g myResourceGroup -n myUniqueApp --action AllowAnonymous \\
          --facebook-app-id my_fb_id --facebook-app-secret my_fb_secret \\
          --facebook-oauth-scopes public_profile email
"""

helps['webapp identity assign'] = """
    type: command
    short-summary: assign or disable managed service identity to the webapp
    examples:
        - name: assign local identity and assign a reader role to the current resource group.
          text: >
            az webapp identity assign -g MyResourceGroup -n MyUniqueApp --role reader --scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/MyResourceGroup
        - name: enable identity for the webapp.
          text: >
            az webapp identity assign -g MyResourceGroup -n MyUniqueApp
"""

helps['webapp identity'] = """
    type: group
    short-summary: manage webapp's managed service identity
"""

helps['webapp identity show'] = """
    type: command
    short-summary: display webapp's managed service identity
"""

helps['webapp identity remove'] = """
    type: command
    short-summary: Disable webapp's managed service identity
"""

helps['functionapp identity'] = helps['webapp identity'].replace('webapp', 'functionapp')

helps['functionapp identity assign'] = helps['webapp identity assign'].replace('webapp', 'functionapp')

helps['functionapp identity show'] = helps['webapp identity show'].replace('webapp', 'functionapp')

helps['functionapp identity remove'] = helps['webapp identity remove'].replace('webapp', 'functionapp')

helps['webapp config'] = """
type: group
short-summary: Configure a web app.
"""

helps['webapp config show'] = """
type: command
short-summary: Get the details of a web app's configuration.
"""

helps['webapp config set'] = """
type: command
short-summary: Set a web app's configuration.
"""

helps['webapp config appsettings'] = """
type: group
short-summary: Configure web app settings.
"""

helps['webapp config appsettings delete'] = """
type: command
short-summary: Delete web app settings.
"""

helps['webapp config appsettings list'] = """
type: command
short-summary: Get the details of a web app's settings.
"""

helps['webapp config appsettings set'] = """
type: command
short-summary: Set a web app's settings.
examples:
    - name: Set the default NodeJS version to 6.9.1 for a web app.
      text: >
        az webapp config appsettings set -g MyResourceGroup -n MyUniqueApp --settings WEBSITE_NODE_DEFAULT_VERSION=6.9.1
"""

helps['webapp config connection-string'] = """
type: group
short-summary: Manage a web app's connection strings.
"""

helps['webapp config connection-string list'] = """
type: command
short-summary: Get a web app's connection strings.
"""

helps['webapp config connection-string delete'] = """
type: command
short-summary: Delete a web app's connection strings.
"""

helps['webapp config connection-string set'] = """
type: command
short-summary: Update a web app's connection strings.
examples:
    - name: Add a mysql connection string.
      text: >
        az webapp config connection-string set -g MyResourceGroup -n MyUniqueApp -t mysql \\
            --settings mysql1='Server=myServer;Database=myDB;Uid=myUser;Pwd=myPwd;'
"""

helps['webapp config container'] = """
type: group
short-summary: Manage web app container settings.
"""

helps['webapp config container show'] = """
type: command
short-summary: Get details of a web app container's settings.
"""

helps['webapp config container set'] = """
type: command
short-summary: Set a web app container's settings.
"""

helps['webapp config container delete'] = """
type: command
short-summary: Delete a web app container's settings.
"""

helps['webapp config ssl'] = """
type: group
short-summary: Configure SSL certificates for web apps.
"""

helps['webapp config ssl list'] = """
type: command
short-summary: List SSL certificates for a web app.
"""

helps['webapp config ssl bind'] = """
type: command
short-summary: Bind an SSL certificate to a web app.
"""

helps['webapp config ssl unbind'] = """
type: command
short-summary: Unbind an SSL certificate from a web app.
"""

helps['webapp config ssl delete'] = """
type: command
short-summary: Delete an SSL certificate from a web app.
"""

helps['webapp config ssl upload'] = """
type: command
short-summary: Upload an SSL certificate to a web app.
"""

helps['webapp deployment'] = """
type: group
short-summary: Manage web app deployments.
"""

helps['webapp deployment slot'] = """
type: group
short-summary: Manage web app deployment slots.
"""

helps['webapp deployment slot auto-swap'] = """
type: group
short-summary: Enable or disable auto-swap for a web app deployment slot.
"""

helps['webapp log'] = """
type: group
short-summary: Manage web app logs.
"""

helps['webapp log config'] = """
type: command
short-summary: Configure logging for a web app.
"""

helps['webapp log show'] = """
type: command
short-summary: Get the details of a web app's logging configuration.
"""

helps['webapp log download'] = """
type: command
short-summary: Download a web app's log history as a zip file.
long-summary: This command may not work with web apps running on Linux.
"""

helps['webapp log tail'] = """
type: command
short-summary: Start live log tracing for a web app.
long-summary: This command may not work with web apps running on Linux.
"""

helps['webapp deployment'] = """
type: group
short-summary: Manage web app deployments.
"""

helps['webapp deployment list-publishing-profiles'] = """
type: command
short-summary: Get the details for available web app deployment profiles.
"""

helps['webapp deployment container'] = """
type: group
short-summary: Manage container-based continuous deployment.
"""

helps['webapp deployment container config'] = """
type: command
short-summary: Configure continuous deployment via containers.
"""

helps['webapp deployment container show-cd-url'] = """
type: command
short-summary: Get the URL which can be used to configure webhooks for continuous deployment.
"""

helps['webapp deployment slot auto-swap'] = """
type: command
short-summary: Configure deployment slot auto swap.
"""

helps['webapp deployment slot create'] = """
type: command
short-summary: Create a deployment slot.
"""

helps['webapp deployment slot swap'] = """
type: command
short-summary: Change deployment slots for a web app.
examples:
    - name: Swap a staging slot into production for the MyUniqueApp web app.
      text: >
        az webapp deployment slot swap  -g MyResourceGroup -n MyUniqueApp --slot staging \\
            --target-slot production
"""

helps['webapp deployment slot list'] = """
type: command
short-summary: List all deployment slots.
"""

helps['webapp deployment slot delete'] = """
type: command
short-summary: Delete a deployment slot.
"""

helps['webapp deployment user'] = """
type: group
short-summary: Manage user credentials for deployment.
"""

helps['webapp deployment user set'] = """
type: command
short-summary: Update deployment credentials.
long-summary: All function and web apps in the subscription will be impacted since they share
              the same deployment credentials.
examples:
    - name: Set FTP and git deployment credentials for all apps.
      text: >
        az webapp deployment user set --user-name MyUserName
"""

helps['webapp deployment slot'] = """
type: group
short-summary: Manage web app deployment slots.
"""

helps['webapp deployment source'] = """
    type: group
    short-summary: Manage web app deployment via source control.
"""

helps['webapp deployment source config'] = """
    type: command
    short-summary: Manage deployment from git or Mercurial repositories.
"""

helps['webapp deployment source config-local-git'] = """
    type: command
    short-summary: Get a URL for a git repository endpoint to clone and push to for web app deployment.
    examples:
        - name: Get an endpoint and add it as a git remote.
          text: >
            az webapp source-control config-local-git \\
                -g MyResourceGroup -n MyUniqueApp

            git remote add azure \\
                https://<deploy_user_name>@MyUniqueApp.scm.azurewebsites.net/MyUniqueApp.git
"""

helps['webapp deployment source config-zip'] = """
    type: command
    short-summary: Perform deployment using the kudu zip push deployment for a webapp.
    long-summary: >
        By default Kudu assumes that zip deployments do not require any build-related actions like
        npm install or dotnet publish. This can be overridden by including a .deployment file in your
        zip file with the following content '[config] SCM_DO_BUILD_DURING_DEPLOYMENT = true',
        to enable Kudu detection logic and build script generation process.
        See https://github.com/projectkudu/kudu/wiki/Configurable-settings#enabledisable-build-actions-preview.
        Alternately the setting can be enabled using the az webapp config appsettings set command.
    examples:
         - name: Perform deployment by using zip file content.
           text: >
             az webapp deployment source config-zip \\
                 -g <myRG> -n <myAppName> \\
                 --src <zip file path location>
"""

helps['webapp deployment source delete'] = """
    type: command
    short-summary: Delete a source control deployment configuration.
"""

helps['webapp deployment source show'] = """
    type: command
    short-summary: Get the details of a source control deployment configuration.
"""

helps['webapp deployment source sync'] = """
    type: command
    short-summary: Synchronize from the repository. Only needed under manual integration mode.
"""

helps['webapp traffic-routing'] = """
    type: group
    short-summary: Manage traffic routing for web apps.
"""

helps['webapp traffic-routing set'] = """
    type: command
    short-summary: Configure routing traffic to deployment slots.
"""

helps['webapp traffic-routing show'] = """
    type: command
    short-summary: Display the current distribution of traffic across slots.
"""

helps['webapp traffic-routing clear'] = """
    type: command
    short-summary: Clear the routing rules and send all traffic to production.
"""

helps['appservice plan'] = """
    type: group
    short-summary: Manage app service plans.
"""

helps['appservice list-locations'] = """
    type: command
    short-summary: List regions where a plan sku is available.
"""

helps['appservice plan update'] = """
    type: command
    short-summary: Update an app service plan.
"""

helps['appservice plan create'] = """
    type: command
    short-summary: Create an app service plan.
    examples:
        - name: Create a basic app service plan.
          text: >
            az appservice plan create -g MyResourceGroup -n MyPlan
        - name: Create a standard app service plan with with four Linux workers.
          text: >
            az appservice plan create -g MyResourceGroup -n MyPlan \\
                --is-linux --number-of-workers 4 --sku S1
"""

helps['appservice plan delete'] = """
    type: command
    short-summary: Delete an app service plan.
"""

helps['appservice plan list'] = """
    type: command
    short-summary: List app service plans.
    examples:
        - name: List all free tier App Service plans.
          text: >
            az appservice plan list --query "[?sku.tier=='Free']"
"""

helps['appservice plan show'] = """
    type: command
    short-summary: Get the app service plans for a resource group or a set of resource groups.
"""

helps['webapp config hostname'] = """
type: group
short-summary: Configure hostnames for a web app.
"""

helps['webapp config hostname add'] = """
    type: command
    short-summary: Bind a hostname to a web app.
"""

helps['webapp config hostname delete'] = """
    type: command
    short-summary: Unbind a hostname from a web app.
"""

helps['webapp config hostname list'] = """
    type: command
    short-summary: List all hostname bindings for a web app.
"""

helps['webapp config hostname get-external-ip'] = """
    type: command
    short-summary: Get the external-facing IP address for a web app.
"""

helps['webapp config backup'] = """
    type: group
    short-summary: Manage backups for web apps.
"""

helps['webapp config backup list'] = """
    type: command
    short-summary: List backups of a web app.
"""

helps['webapp config backup create'] = """
    type: command
    short-summary: Create a backup of a web app.
"""

helps['webapp config backup show'] = """
    type: command
    short-summary: Show the backup schedule for a web app.
"""

helps['webapp config backup update'] = """
    type: command
    short-summary: Configure a new backup schedule for a web app.
"""

helps['webapp config backup restore'] = """
    type: command
    short-summary: Restore a web app from a backup.
"""

helps['webapp browse'] = """
    type: command
    short-summary: Open a web app in a browser.
"""

helps['webapp create'] = """
    type: command
    short-summary: Create a web app.
    long-summary: The web app's name must be able to produce a unique FQDN as AppName.azurewebsites.net.
    examples:
        - name: Create a web app with the default configuration.
          text: >
            az webapp create -g MyResourceGroup -p MyPlan -n MyUniqueAppName
        - name: Create a web app with a NodeJS 6.2 runtime and deployed from a local git repository.
          text: >
            az webapp create -g MyResourceGroup -p MyPlan -n MyUniqueAppName --runtime "node|6.2" --deployment-local-git
"""

helps['webapp update'] = """
    type: command
    short-summary: Update a web app.
    examples:
        - name: Update the tags of a web app.
          text: >
            az webapp update -g MyResourceGroup -n MyAppName --set tags.tagName=tagValue
"""

helps['webapp list-runtimes'] = """
    type: command
    short-summary: List available built-in stacks which can be used for web apps.
"""

helps['webapp delete'] = """
    type: command
    short-summary: Delete a web app.
"""

helps['webapp list'] = """
    type: command
    short-summary: List web apps.
    examples:
        - name: List default host name and state for all web apps.
          text: >
            az webapp list --query "[].{hostName: defaultHostName, state: state}"
        - name: List all running web apps.
          text: >
            az webapp list --query "[?state=='Running']"
"""

helps['webapp restart'] = """
    type: command
    short-summary: Restart a web app.
"""

helps['webapp start'] = """
    type: command
    short-summary: Start a web app.
"""

helps['webapp show'] = """
    type: command
    short-summary: Get the details of a web app.
"""

helps['webapp stop'] = """
    type: command
    short-summary: Stop a web app.
"""

helps['functionapp'] = """
    type: group
    short-summary: Manage function apps.
"""

helps['functionapp create'] = """
    type: command
    short-summary: Create a function app.
    long-summary: The function app's name must be able to produce a unique FQDN as AppName.azurewebsites.net.
    examples:
        - name: Create a basic function app.
          text: >
            az functionapp create -g MyResourceGroup  -p MyPlan -n MyUniqueAppName -s MyStorageAccount
"""

helps['functionapp update'] = """
    type: command
    short-summary: Update a function app.
"""

helps['functionapp delete'] = """
    type: command
    short-summary: Delete a function app.
"""

helps['functionapp list'] = """
    type: command
    short-summary: List function apps.
    examples:
        - name: List default host name and state for all function apps.
          text: >
            az functionapp list --query "[].{hostName: defaultHostName, state: state}"
        - name: List all running function apps.
          text: >
            az functionapp list --query "[?state=='Running']"
"""

helps['functionapp restart'] = """
    type: command
    short-summary: Restart a function app.
"""

helps['functionapp start'] = """
    type: command
    short-summary: Start a function app.
"""

helps['functionapp show'] = """
    type: command
    short-summary: Get the details of a function app.
"""

helps['functionapp stop'] = """
    type: command
    short-summary: Stop a function app.
"""

helps['functionapp list-consumption-locations'] = """
    type: command
    short-summary: List available locations for running function apps.
"""

helps['functionapp config'] = """
    type: group
    short-summary: Configure a function app.
"""

helps['functionapp config appsettings'] = """
    type: group
    short-summary: Configure function app settings.
"""

helps['functionapp config appsettings list'] = """
    type: command
    short-summary: Show settings for a function app.
"""

helps['functionapp config appsettings set'] = """
    type: command
    short-summary: Update a function app's settings.
"""

helps['functionapp config appsettings delete'] = """
    type: command
    short-summary: Delete a function app's settings.
"""

helps['functionapp config hostname'] = """
    type: group
    short-summary: Configure hostnames for a function app.
"""
helps['functionapp config hostname add'] = """
    type: command
    short-summary: Bind a hostname to a function app.
"""

helps['functionapp config hostname delete'] = """
    type: command
    short-summary: Unbind a hostname from a function app.
"""

helps['functionapp config hostname list'] = """
    type: command
    short-summary: List all hostname bindings for a function app.
"""

helps['functionapp config hostname get-external-ip'] = """
    type: command
    short-summary: Get the external-facing IP address for a function app.
"""

helps['functionapp config ssl'] = """
    type: group
    short-summary: Configure SSL certificates.
"""

helps['functionapp config ssl list'] = """
    type: command
    short-summary: List SSL certificates for a function app.
"""

helps['functionapp config ssl bind'] = """
    type: command
    short-summary: Bind an SSL certificate to a function app.
"""

helps['functionapp config ssl unbind'] = """
    type: command
    short-summary: Unbind an SSL certificate from a function app.
"""

helps['functionapp config ssl delete'] = """
    type: command
    short-summary: Delete an SSL certificate from a function app.
"""

helps['functionapp config ssl upload'] = """
    type: command
    short-summary: Upload an SSL certificate to a function app.
"""

helps['functionapp deployment'] = """
    type: group
    short-summary: Manage function app deployments.
"""

helps['functionapp deployment list-publishing-profiles'] = """
    type: command
    short-summary: Get the details for available function app deployment profiles.
"""

helps['functionapp deployment source'] = """
    type: group
    short-summary: Manage function app deployment via source control.
"""

helps['functionapp deployment source config'] = """
    type: command
    short-summary: Manage deployment from git or Mercurial repositories.
"""

helps['functionapp deployment source config-local-git'] = """
    type: command
    short-summary: Get a URL for a git repository endpoint to clone and push to for function app deployment.
    examples:
        - name: Get an endpoint and add it as a git remote.
          text: >
            az functionapp source-control config-local-git \\
                -g MyResourceGroup -n MyUniqueApp

            git remote add azure \\
                https://<deploy_user_name>@MyUniqueApp.scm.azurewebsites.net/MyUniqueApp.git
"""

helps['functionapp deployment source delete'] = """
    type: command
    short-summary: Delete a source control deployment configuration.
"""

helps['functionapp deployment source show'] = """
    type: command
    short-summary: Get the details of a source control deployment configuration.
"""

helps['functionapp deployment source sync'] = """
    type: command
    short-summary: Synchronize from the repository. Only needed under manual integration mode.
"""

helps['functionapp deployment user'] = """
    type: group
    short-summary: Manage user credentials for deployment.
"""

helps['functionapp deployment user set'] = """
    type: command
    short-summary: Update deployment credentials.
    long-summary: All function and web apps in the subscription will be impacted since they share
                  the same deployment credentials.
    examples:
        - name: Set FTP and git deployment credentials for all apps.
          text: >
            az functionapp deployment user set
            --user-name MyUserName
"""

helps['functionapp deployment source config-zip'] = """
    type: command
    short-summary: Perform deployment using the kudu zip push deployment for a function app.
    long-summary: >
        By default Kudu assumes that zip deployments do not require any build-related actions like
        npm install or dotnet publish. This can be overridden by including an .deployment file in your
        zip file with the following content '[config] SCM_DO_BUILD_DURING_DEPLOYMENT = true',
        to enable Kudu detection logic and build script generation process.
        See https://github.com/projectkudu/kudu/wiki/Configurable-settings#enabledisable-build-actions-preview.
        Alternately the setting can be enabled using the az functionapp config appsettings set command.
    examples:
         - name: Perform deployment by using zip file content.
           text: >
             az functionapp deployment source config-zip \\
                 -g <myRG> -n <myAppName> \\
                 --src <zip file path location>
"""
