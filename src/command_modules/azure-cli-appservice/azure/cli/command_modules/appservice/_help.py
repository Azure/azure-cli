# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['appservice'] = """
    type: group
    short-summary: commands for managing your Azure web apps, app service plans, etc
"""

helps['appservice web config'] = """
    type: group
    short-summary: commands to configure the web app
"""

helps['appservice web config show'] = """
    type: command
    short-summary: show web app configurations
"""

helps['appservice web config update'] = """
    type: command
    short-summary: update web app configurations
"""

helps['appservice web config appsettings'] = """
    type: group
    short-summary: commands to configure application settings
"""

helps['appservice web config appsettings show'] = """
    type: command
    short-summary: show application settings
"""

helps['appservice web config appsettings update'] = """
    type: command
    short-summary: create or update application settings
"""

helps['appservice web config appsettings delete'] = """
    type: command
    short-summary: delete application settings
"""

helps['appservice web config container'] = """
    type: group
    short-summary: commands to configure container specific application settings
"""

helps['appservice web config container show'] = """
    type: command
    short-summary: show container settings
"""

helps['appservice web config container update'] = """
    type: command
    short-summary: update container settings
"""

helps['appservice web config container delete'] = """
    type: command
    short-summary: delete container settings
"""

helps['appservice web config hostname'] = """
    type: group
    short-summary: commands to configure hostnames
"""

helps['appservice web log'] = """
    type: group
    short-summary: commands to manage logs 
"""

helps['appservice web deployment'] = """
    type: group
    short-summary: commands to manage deployments (slots, credentials, etc)
"""

helps['appservice web deployment list-site-credentials'] = """
    type: command
    short-summary: show site level deployment credentials
"""

helps['appservice web deployment slot auto-swap'] = """
    type: command
    short-summary: configure slot auto swap
"""

helps['appservice web deployment slot create'] = """
    type: command
    short-summary: create a slot
"""

helps['appservice web deployment slot swap'] = """
    type: command
    short-summary: swap slots
"""

helps['appservice web deployment slot list'] = """
    type: command
    short-summary: list all slots
"""

helps['appservice web deployment slot delete'] = """
    type: command
    short-summary: delete a slot
"""

helps['appservice web deployment user'] = """
    type: group
    short-summary: commands to manage deployment user credentials
"""

helps['appservice web deployment slot'] = """
    type: group
    short-summary: commands to manage deployment slots
"""

helps['appservice web source-control'] = """
    type: group
    short-summary: commands to manage source control systems
"""

helps['appservice web source-control config'] = """
    type: command
    short-summary: associate to Git or Mercurial repositories
"""

helps['appservice web source-control config-local-git'] = """
    type: command
    short-summary: enable local git, you will get a url to clone and later push to the web app
"""

helps['appservice web source-control delete'] = """
    type: command
    short-summary: delete source control configurations.
"""

helps['appservice web source-control show'] = """
    type: command
    short-summary: show source control configurations.
"""

helps['appservice web source-control sync'] = """
    type: command
    short-summary: synchronize from the source repository, only needed under maunal integration mode.
"""

helps['appservice plan update'] = """
    type: command
    short-summary: update plan, including 'scale up' and 'scale out'
"""

helps['appservice plan create'] = """
    type: command
    short-summary: create a new plan
"""

helps['appservice web config hostname add'] = """
    type: command
    short-summary: bind a hostname(custom domain) to the web app
"""

helps['appservice web config hostname delete'] = """
    type: command
    short-summary: unbind a hostname(custom domain) from the web app
"""

helps['appservice web config hostname list'] = """
    type: command
    short-summary: list all hostname bindings
"""

helps['appservice web browse'] = """
    type: command
    short-summary: Open the web app in a browser
"""

helps['appservice web create'] = """
    type: command
    short-summary: create a web app
"""

helps['appservice web delete'] = """
    type: command
    short-summary: delete a web app
"""

helps['appservice web list'] = """
    type: command
    short-summary: list web apps
"""

helps['appservice web restart'] = """
    type: command
    short-summary: restart a web app
"""

helps['appservice web show'] = """
    type: command
    short-summary: show a web app
"""

helps['appservice web stop'] = """
    type: command
    short-summary: stop a web app
"""
