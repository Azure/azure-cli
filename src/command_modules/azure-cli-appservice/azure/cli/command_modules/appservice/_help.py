# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['appservice'] = """
    type: group
    short-summary: Manage your App Service plans.
"""

helps['appservice web'] = """
    type: group
    short-summary: deprecated, please use 'az webapp'.
"""

helps['webapp'] = """
    type: group
    short-summary: Manage web apps.
"""

helps['webapp config'] = """
    type: group
    short-summary: Configure a web app.
"""

helps['webapp config show'] = """
    type: command
    short-summary: Show web app configurations.
"""

helps['webapp config set'] = """
    type: command
    short-summary: create or update web app configurations.
"""

helps['webapp config appsettings'] = """
    type: group
    short-summary: Configure web app settings.
"""

helps['webapp config appsettings show'] = """
    type: command
    short-summary: Show web app settings.
"""

helps['webapp config appsettings set'] = """
    type: command
    short-summary: Create or update web app settings.
    examples:
        - name: Set the default node version for a specified web app.
          text: >
            az webapp config appsettings set
            -g MyResourceGroup
            -n MyUniqueApp
            --settings WEBSITE_NODE_DEFAULT_VERSION=6.9.1
"""

helps['webapp config connection-string'] = """
    type: group
    short-summary: Configure web app connection strings.
"""

helps['webapp config connection-string show'] = """
    type: command
    short-summary: Show connection strings
"""

helps['webapp config connection-string delete'] = """
    type: command
    short-summary: delete connection strings
"""

helps['webapp config connection-string set'] = """
    type: command
    short-summary: Create or update connection strings.
    examples:
        - name: add a mysql connection string.
          text: >
            az webapp config connection-string set
            -g MyResourceGroup
            -n MyUniqueApp
            -t mysql
            --settings mysql1='Server=myServer;Database=myDB;Uid=myUser;Pwd=myPwd;'
"""

helps['webapp config container'] = """
    type: group
    short-summary: Configure container specific settings.
"""

helps['webapp config container show'] = """
    type: command
    short-summary: Show container settings.
"""

helps['webapp config container set'] = """
    type: command
    short-summary: create or update container settings.
"""

helps['webapp config container delete'] = """
    type: command
    short-summary: Delete container settings.
"""

helps['webapp config hostname'] = """
    type: group
    short-summary: Configure hostnames.
"""

helps['webapp config ssl'] = """
    type: group
    short-summary: Configure SSL certificates.
"""

helps['webapp config ssl list'] = """
    type: command
    short-summary: List SSL certificates within a resource group
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

helps['webapp deployment source'] = """
    type: group
    short-summary: Manage deployment source repositories.
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
    short-summary: Configure web app logs.
"""

helps['webapp log download'] = """
    type: command
    short-summary: Download historical logs as a zip file
    long-summary: Might not work with Linux webs
"""

helps['webapp log tail'] = """
    type: command
    short-summary: Start live tracing
    long-summary: Might not work with Linux webs
"""

helps['webapp deployment'] = """
    type: group
    short-summary: Manage web application deployments.
"""

helps['webapp deployment list-publishing-profiles'] = """
    type: command
    short-summary: get publishing endpoints, credentials, database connection strings, etc
"""

helps['webapp deployment slot auto-swap'] = """
    type: command
    short-summary: Configure slot auto swap.
"""

helps['webapp deployment slot create'] = """
    type: command
    short-summary: Create a slot.
"""

helps['webapp deployment slot swap'] = """
    type: command
    short-summary: Swap slots.
    examples:
        - name: Swap a staging slot into production for the specified web app.
          text: >
            az webapp deployment slot swap
            -g MyResourceGroup
            -n MyUniqueApp
            --slot staging
            --target-slot production
"""

helps['webapp deployment slot list'] = """
    type: command
    short-summary: List all slots.
"""

helps['webapp deployment slot delete'] = """
    type: command
    short-summary: Delete a slot.
"""

helps['webapp deployment user'] = """
    type: group
    short-summary: Manage user credentials for a deployment.
"""

helps['webapp deployment user set'] = """
    type: command
    short-summary: Update deployment credentials.
    long-summary: All web apps in the subscription will be impacted since all web apps share
                  the same deployment credentials.
    examples:
        - name: Set FTP and git deployment credentials for all web apps.
          text: >
            az webapp deployment user set
            --user-name MyUserName
"""

helps['webapp deployment slot'] = """
    type: group
    short-summary: Manage deployment slots.
"""

helps['webapp deployment source'] = """
    type: group
    short-summary: Manage source control systems.
"""

helps['webapp deployment source config'] = """
    type: command
    short-summary: Associate to Git or Mercurial repositories.
"""

helps['webapp deployment source config-local-git'] = """
    type: command
    short-summary: Enable local git.
    long-summary: Get an endpoint to clone and later push to the web app.
    examples:
        - name: Get a git endpoint for a web app and add it as a remote.
          text: >
            az webapp source-control config-local-git \\
                -g MyResourceGroup -n MyUniqueApp

            git remote add azure \\
                https://<deploy_user_name>@MyUniqueApp.scm.azurewebsites.net/MyUniqueApp.git
"""

helps['webapp deployment source delete'] = """
    type: command
    short-summary: Delete source control configurations.
"""

helps['webapp deployment source show'] = """
    type: command
    short-summary: Show source control configurations.
"""

helps['webapp deployment source sync'] = """
    type: command
    short-summary: Synchronize from the source repository, only needed under manual integration mode.
"""

helps['webapp traffic-routing'] = """
    type: group
    short-summary: Manage traffic routings in production test.
"""

helps['webapp traffic-routing'] = """
    type: group
    short-summary: Manage traffic routings in production test.
"""

helps['webapp traffic-routing set'] = """
    type: command
    short-summary: Routing some percentages of traffic to deployment slots
"""

helps['webapp traffic-routing show'] = """
    type: command
    short-summary: Display the current distribution of traffic across slots
"""

helps['webapp traffic-routing clear'] = """
    type: command
    short-summary: Clear the routing rules to send 100% to production
"""

helps['appservice plan'] = """
    type: group
    short-summary: Manage App Service plans.
"""

helps['appservice plan update'] = """
    type: command
    short-summary: Update an App Service plan.
"""

helps['appservice plan create'] = """
    type: command
    short-summary: Create an App Service plan.
    examples:
        - name: Create a basic App Service plan.
          text: >
            az appservice plan create -g MyResourceGroup -n MyPlan
        - name: Create a standard App Service plan with with four Linux workers.
          text: >
            az appservice plan create
            -g MyResourceGroup
            -n MyPlan
            --is-linux
            --number-of-workers 4
            --sku S1
"""

helps['appservice plan delete'] = """
    type: command
    short-summary: Delete an App Service plan.
"""

helps['appservice plan list'] = """
    type: command
    short-summary: List App Service plans.
    examples:
        - name: List all free tier App Service plans.
          text: >
            az appservice plan list --query "[?sku.tier=='Free']"
"""

helps['appservice plan show'] = """
    type: command
    short-summary: Get the App Service plans for a resource group or a set of resource groups.
"""

helps['webapp config hostname add'] = """
    type: command
    short-summary: Bind a hostname (custom domain) to a web app.
"""

helps['webapp config hostname delete'] = """
    type: command
    short-summary: Unbind a hostname (custom domain) from a web app.
"""

helps['webapp config hostname list'] = """
    type: command
    short-summary: List all hostname bindings.
"""

helps['webapp config hostname get-external-ip'] = """
    type: command
    short-summary: get the ip address to configure your DNS settings for A records
"""

helps['webapp config backup list'] = """
    type: command
    short-summary: List all backups of a web app.
"""

helps['webapp config backup create'] = """
    type: command
    short-summary: Create a backup of a web app.
"""

helps['webapp config backup show'] = """
    type: command
    short-summary: Show the backup schedule of a web app.
"""

helps['webapp config backup update'] = """
    type: command
    short-summary: Configure a new backup schedule.
"""

helps['webapp config backup restore'] = """
    type: command
    short-summary: Restore a web app from a backup.
"""

helps['webapp browse'] = """
    type: command
    short-summary: Open the web app in a browser.
"""

helps['webapp create'] = """
    type: command
    short-summary: Create a web app.
    examples:
        - name: Create an empty webapp.  Name must be unique to yield a unique FQDN;
                for example, MyUniqueApp.azurewebsites.net.
          text: >
            az webapp create -g MyResourceGroup -p MyPlan -n MyUniqueApp
        - name: Create a webapp with node 6.2 stack runtime, and local git configured for web deployment
          text: >
            az webapp create -g MyResourceGroup -p MyPlan -n MyUniqueApp --runtime "node|6.2" --deployment-local-git
"""

helps['webapp list-runtimes'] = """
    type: command
    short-summary: List built-in web stack runtimes you can use to create new webapps.
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
            az webapp list --query "[].{ hostName: defaultHostName, state: state }"
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
    short-summary: Show a web app.
"""

helps['webapp stop'] = """
    type: command
    short-summary: Stop a web app.
"""

helps['webapp production-test'] = """
    type: command
    short-summary: test in production, including configuring static routings.
"""

helps['functionapp'] = """
    type: group
    short-summary: Manage your function app.
"""

helps['functionapp create'] = """
    type: command
    short-summary: Create a function app.
    examples:
        - name: Create a basic function app.  Name must be unique to yield a unique FQDN;
                for example, MyUniqueApp.azurewebsites.net.
          text: >
            az functionapp create
            -g MyResourceGroup
            -p MyPlan
            -n MyUniqueApp
            -s MyStorageAccount
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
            az functionapp list --query "[].{ hostName: defaultHostName, state: state }"
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
    short-summary: Show a function app.
"""

helps['functionapp stop'] = """
    type: command
    short-summary: Stop a function app.
"""

helps['functionapp config'] = """
    type: group
    short-summary: Configure a function app.
"""

helps['functionapp config appsettings'] = """
    type: group
    short-summary: Configure function app settings.
"""

helps['functionapp config appsettings show'] = """
    type: command
    short-summary: Show function app settings.
"""

helps['functionapp config appsettings set'] = """
    type: command
    short-summary: Create or update function app settings.
"""

helps['functionapp config hostname'] = """
    type: group
    short-summary: Configure hostnames.
"""
helps['functionapp config hostname add'] = """
    type: command
    short-summary: Bind a hostname (custom domain) to a function app.
"""

helps['functionapp config hostname delete'] = """
    type: command
    short-summary: Unbind a hostname (custom domain) from a function app.
"""

helps['functionapp config hostname list'] = """
    type: command
    short-summary: List all hostname bindings.
"""

helps['functionapp config hostname get-external-ip'] = """
    type: command
    short-summary: get the ip address to configure your DNS settings for A records
"""

helps['functionapp config ssl'] = """
    type: group
    short-summary: Configure SSL certificates.
"""

helps['functionapp config ssl list'] = """
    type: command
    short-summary: List SSL certificates within a resource group
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
helps['functionapp deployment source'] = """
    type: group
    short-summary: Manage source control systems.
"""

helps['functionapp deployment source config'] = """
    type: command
    short-summary: Associate to Git or Mercurial repositories.
"""

helps['functionapp deployment source config-local-git'] = """
    type: command
    short-summary: Enable local git.
    long-summary: Get an endpoint to clone and later push to the function app.
    examples:
        - name: Get a git endpoint for a web app and add it as a remote.
          text: >
            az functionapp source-control config-local-git \\
                -g MyResourceGroup -n MyUniqueApp

            git remote add azure \\
                https://<deploy_user_name>@MyUniqueApp.scm.azurewebsites.net/MyUniqueApp.git
"""

helps['functionapp deployment source delete'] = """
    type: command
    short-summary: Delete source control configurations.
"""

helps['functionapp deployment source show'] = """
    type: command
    short-summary: Show source control configurations.
"""

helps['functionapp deployment source sync'] = """
    type: command
    short-summary: Synchronize from the source repository, only needed under manual integration mode.
"""
helps['functionapp deployment user'] = """
    type: group
    short-summary: Manage user credentials for a deployment.
"""

helps['functionapp deployment user set'] = """
    type: command
    short-summary: Update deployment credentials.
    long-summary: All function/web apps in the subscription will be impacted since all apps share
                  the same deployment credentials.
    examples:
        - name: Set FTP and git deployment credentials for all function/web apps.
          text: >
            az functionapp deployment user set
            --user-name MyUserName
"""
