# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['appservice'] = """
    type: group
    short-summary: Manage your Azure Web apps and App Service plans.
"""

helps['appservice web'] = """
    type: group
    short-summary: Manage web apps.
"""

helps['appservice web config'] = """
    type: group
    short-summary: Configure a web app.
"""

helps['appservice web config show'] = """
    type: command
    short-summary: Show web app configurations.
"""

helps['appservice web config update'] = """
    type: command
    short-summary: Update web app configurations.
"""

helps['appservice web config appsettings'] = """
    type: group
    short-summary: Configure web app settings.
"""

helps['appservice web config appsettings show'] = """
    type: command
    short-summary: Show web app settings.
"""

helps['appservice web config appsettings update'] = """
    type: command
    short-summary: Create or update web app settings.
    examples:
        - name: Set the default node version for a specified web app.
          text: >
            az appservice web config appsettings update
            -g MyResourceGroup
            -n MyUniqueApp
            --settings WEBSITE_NODE_DEFAULT_VERSION=6.9.1
"""

helps['appservice web config appsettings delete'] = """
    type: command
    short-summary: Delete web app settings.
"""

helps['appservice web config container'] = """
    type: group
    short-summary: Configure container specific settings.
"""

helps['appservice web config container show'] = """
    type: command
    short-summary: Show container settings.
"""

helps['appservice web config container update'] = """
    type: command
    short-summary: Update container settings.
"""

helps['appservice web config container delete'] = """
    type: command
    short-summary: Delete container settings.
"""

helps['appservice web config hostname'] = """
    type: group
    short-summary: Configure hostnames.
"""

helps['appservice web config ssl'] = """
    type: group
    short-summary: Configure SSL certificates.
"""

helps['appservice web config ssl upload'] = """
    type: command
    short-summary: Upload an SSL certificate to a web app.
"""

helps['appservice web config ssl list'] = """
    type: command
    short-summary: List SSL certificates.
"""

helps['appservice web config ssl bind'] = """
    type: command
    short-summary: Bind an SSL certificate to a web app.
"""

helps['appservice web config ssl unbind'] = """
    type: command
    short-summary: Unbind an SSL certificate from a web app.
"""

helps['appservice web config ssl delete'] = """
    type: command
    short-summary: Delete an SSL certificate from a web app.
"""

helps['appservice web deployment'] = """
    type: group
    short-summary: Manage web app deployments.
"""

helps['appservice web deployment slot'] = """
    type: group
    short-summary: Manage web app deployment slots.
"""

helps['appservice web deployment slot auto-swap'] = """
    type: group
    short-summary: Enable or disable auto-swap for a web app deployment slot.
"""

helps['appservice web log'] = """
    type: group
    short-summary: Manage web app logs.
"""

helps['appservice web log config'] = """
    type: command
    short-summary: Configure web app logs.
"""

helps['appservice web deployment'] = """
    type: group
    short-summary: Manage web application deployments.
"""

helps['appservice web deployment list-site-credentials'] = """
    type: command
    short-summary: Show site-level deployment credentials.
"""

helps['appservice web deployment slot auto-swap'] = """
    type: command
    short-summary: Configure slot auto swap.
"""

helps['appservice web deployment slot create'] = """
    type: command
    short-summary: Create a slot.
"""

helps['appservice web deployment slot swap'] = """
    type: command
    short-summary: Swap slots.
    examples:
        - name: Swap a staging slot into production for the specified web app.
          text: >
            az appservice web deployment slot swap
            -g MyResourceGroup
            -n MyUniqueApp
            --slot staging
            --target-slot production
"""

helps['appservice web deployment slot list'] = """
    type: command
    short-summary: List all slots.
"""

helps['appservice web deployment slot delete'] = """
    type: command
    short-summary: Delete a slot.
"""

helps['appservice web deployment user'] = """
    type: group
    short-summary: Manage user credentials for a deployment.
"""

helps['appservice web deployment user set'] = """
    type: command
    short-summary: Update deployment credentials.
    long-summary: All web apps in the subscription will be impacted since all web apps share
                  the same deployment credentials.
    examples:
        - name: Set FTP and git deployment credentials for all web apps.
          text: >
            az appservice web deployment user set
            --user-name MyUserName
"""

helps['appservice web deployment slot'] = """
    type: group
    short-summary: Manage deployment slots.
"""

helps['appservice web source-control'] = """
    type: group
    short-summary: Manage source control systems.
"""

helps['appservice web source-control config'] = """
    type: command
    short-summary: Associate to Git or Mercurial repositories.
"""

helps['appservice web source-control config-local-git'] = """
    type: command
    short-summary: Enable local git.
    long-summary: Get an endpoint to clone and later push to the web app.
    examples:
        - name: Get a git endpoint for a web app and add it as a remote.
          text: >
            az appservice web source-control config-local-git \\
                -g MyResourceGroup -n MyUniqueApp

            git remote add azure \\
                https://<deploy_user_name>@MyUniqueApp.scm.azurewebsites.net/MyUniqueApp.git
"""

helps['appservice web source-control delete'] = """
    type: command
    short-summary: Delete source control configurations.
"""

helps['appservice web source-control show'] = """
    type: command
    short-summary: Show source control configurations.
"""

helps['appservice web source-control sync'] = """
    type: command
    short-summary: Synchronize from the source repository, only needed under maunal integration mode.
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

helps['appservice web config hostname add'] = """
    type: command
    short-summary: Bind a hostname (custom domain) to a web app.
"""

helps['appservice web config hostname delete'] = """
    type: command
    short-summary: Unbind a hostname (custom domain) from a web app.
"""

helps['appservice web config hostname list'] = """
    type: command
    short-summary: List all hostname bindings.
"""

helps['appservice web config backup list'] = """
    type: command
    short-summary: List all backups of a web app.
"""

helps['appservice web config backup create'] = """
    type: command
    short-summary: Create a backup of a web app.
"""

helps['appservice web config backup show'] = """
    type: command
    short-summary: Show the backup schedule of a web app.
"""

helps['appservice web config backup update'] = """
    type: command
    short-summary: Configure a new backup schedule.
"""

helps['appservice web config backup restore'] = """
    type: command
    short-summary: Restore a web app from a backup.
"""

helps['appservice web browse'] = """
    type: command
    short-summary: Open the web app in a browser.
"""

helps['appservice web create'] = """
    type: command
    short-summary: Create a web app.
    examples:
        - name: Create a basic App Service plan.  Name must be unique to yield a unique FQDN;
                for example, MyUniqueApp.azurewebsites.net.
          text: >
            az appservice web create
            -g MyResourceGroup
            -p MyPlan
            -n MyUniqueApp
"""

helps['appservice web delete'] = """
    type: command
    short-summary: Delete a web app.
"""

helps['appservice web list'] = """
    type: command
    short-summary: List web apps.
    examples:
        - name: List default host name and state for all web apps.
          text: >
            az appservice web list --query "[].{ hostName: defaultHostName, state: state }"
        - name: List all running web apps.
          text: >
            az appservice web list --query "[?state=='Running']"
"""

helps['appservice web restart'] = """
    type: command
    short-summary: Restart a web app.
"""

helps['appservice web start'] = """
    type: command
    short-summary: Start a web app.
"""

helps['appservice web show'] = """
    type: command
    short-summary: Show a web app.
"""

helps['appservice web stop'] = """
    type: command
    short-summary: Stop a web app.
"""
