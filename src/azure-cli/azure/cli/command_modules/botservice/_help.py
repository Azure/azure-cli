# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['bot'] = """
    type: group
    short-summary: Manage Microsoft Azure Bot Service.
"""
helps['bot create'] = """
    type: command
    short-summary: Create a new v4 SDK bot.
    long-summary: Create a new v4 SDK bot.
"""
helps['bot show'] = """
    type: command
    short-summary: Get an existing bot.
    long-summary: Get information about an existing bot. To get the information needed to connect to the bot, use the
                  --msbot flag with the command.
    examples:
    - name: Get the information needed to connect to an existing bot on Azure
      text: |-
        az bot show -n botName -g MyResourceGroup --msbot
"""
helps['bot prepare-publish'] = """
    type: command
    short-summary: (Maintenance mode) Add scripts to your local source code directory to
                   be able to publish back using `az bot publish` for v3 SDK bots.
"""
helps['bot prepare-deploy'] = """
    type: command
    short-summary: Add scripts/config files for publishing with `az webapp deployment`.
    long-summary: Add scripts or configuration files to the root of your local source code directory to be able to
                  publish using `az webapp deployment`. When your code is deployed to your App Service, the generated
                  scripts or configuration files should be appear in D:\\home\\site\\wwwroot on App Service's Kudu web
                  page.
    examples:
        - name: Prepare to use `az webapp` to deploy a Javascript bot by fetching a Node.js IIS web.config file.
          text: |-
            az bot prepare-deploy --lang Javascript --code-dir "MyBotCode"
        - name: Prepare to use `az webapp` to deploy a Csharp bot by creating a .deployment file.
          text: |-
            az bot prepare-deploy --lang Csharp --code-dir "." --proj-file-path "MyBot.csproj"
"""
helps['bot delete'] = """
    type: command
    short-summary: Delete an existing bot.
"""
helps['bot update'] = """
    type: command
    short-summary: Update an existing bot.
    examples:
        - name: Update description on a bot
          text: |-
            az bot update -n botName -g MyResourceGroup --endpoint "https://bing.com/api/messages" --display-name "Hello World"
"""
helps['bot publish'] = """
    type: command
    short-summary: Publish to a bot's associated app service.
    long-summary: Publish your source code to your bot's associated app service. This is DEPRECATED for v4 bots and no
                  longer recommended for publishing v4 bots to Azure. Instead use `az bot prepare-deploy` and `az webapp
                  deployment` to deploy your v4 bot. For more information see https://aka.ms/deploy-your-bot.
    examples:
        - name: Publish source code to your Azure App, from within the bot code folder
          text: |-
            az bot publish -n botName -g MyResourceGroup
"""
helps['bot download'] = """
    type: command
    short-summary: Download an existing bot.
    long-summary: The source code is downloaded from the web app associated with the bot.
                  You can then make changes to it and publish it back to your app.
"""
helps['bot facebook create'] = """
    type: command
    short-summary: Create the Facebook Channel on a bot.
    examples:
        - name: Create the Facebook Channel for a bot
          text: |
            az bot facebook create -n botName -g MyResourceGroup --appid myAppId \\
            --page-id myPageId --secret mySecret --token myToken
"""
helps['bot email create'] = """
    type: command
    short-summary: Create the Email Channel on a bot.
    examples:
        - name: Create the Email Channel for a bot
          text: |-
            az bot email create -n botName -g MyResourceGroup -a abc@outlook.com \\
            -p password
"""
helps['bot msteams create'] = """
    type: command
    short-summary: Create the Microsoft Teams Channel on a bot.
    examples:
        - name: Create the Microsoft Teams Channel for a bot with calling enabled
          text: |-
            az bot msteams create -n botName -g MyResourceGroup --enable-calling
            --calling-web-hook https://www.myapp.com/
"""
helps['bot skype create'] = """
    type: command
    short-summary: Create the Skype Channel on a bot.
    examples:
        - name: Create the Skype Channel for a bot with messaging and screen sharing enabled
          text: |-
            az bot skype create -n botName -g MyResourceGroup --enable-messaging
            --enable-screen-sharing
"""
helps['bot kik create'] = """
    type: command
    short-summary: Create the Kik Channel on a bot.
    examples:
        - name: Create the Kik Channel for a bot.
          text: |-
            az bot kik create -n botName -g MyResourceGroup -u mykikname \\
            --key key --is-validated
"""
helps['bot directline create'] = """
    type: command
    short-summary: Create the DirectLine Channel on a bot with only v3 protocol enabled.
    examples:
        - name: Create the DirectLine Channel for a bot.
          text: |-
            az bot directline create -n botName -g MyResourceGroup --disablev1
"""
helps['bot directline update'] = """
    type: command
    short-summary: Update the DirectLine Channel on a bot with only v3 protocol enabled.
    examples:
        - name: Update the DirectLine Channel for a bot.
          text: |-
            az bot directline update -n botName -g MyResourceGroup --disablev1
"""
helps['bot telegram create'] = """
    type: command
    short-summary: Create the Telegram Channel on a bot.
    examples:
        - name: Create the Telegram Channel for a bot.
          text: |-
            az bot telegram create -n botName -g MyResourceGroup --access-token token
            --is-validated
"""
helps['bot sms create'] = """
    type: command
    short-summary: Create the SMS Channel on a bot.
    examples:
        - name: Create the SMS Channel for a bot.
          text: |-
            az bot sms create -n botName -g MyResourceGroup --account-sid sid \\
            --auth-token token --is-validated --phone 1234567890
"""
helps['bot slack create'] = """
    type: command
    short-summary: Create the Slack Channel on a bot.
    examples:
        - name: Create the Slack Channel for a bot.
          text: |-
            az bot slack create -n botName -g MyResourceGroup --client-id clientid \\
            --client-secret secret --verification-token token
"""
helps['bot authsetting'] = """
    type: group
    short-summary: Manage OAuth connection settings on a bot.
"""
helps['bot authsetting create'] = """
    type: command
    short-summary: Create an OAuth connection setting on a bot.
    examples:
        - name: Create a new OAuth connection setting on a bot.
          text: |-
            az bot authsetting create -g MyResourceGroup -n botName -c myConnectionName \\
            --client-id clientId --client-secret secret --provider-scope-string "scope1 scope2"\\
            --service google --parameters id=myid
"""
helps['bot authsetting show'] = """
    type: command
    short-summary: Show details of an OAuth connection setting on a bot.
"""
helps['bot authsetting list'] = """
    type: command
    short-summary: Show all OAuth connection settings on a bot.
"""
helps['bot authsetting delete'] = """
    type: command
    short-summary: Delete an OAuth connection setting on a bot.
"""
helps['bot authsetting list-providers'] = """
    type: command
    short-summary: List details for all service providers available for creating OAuth connection settings.
    examples:
        - name: List all service providers.
          text: |-
            az bot authsetting list-providers
        - name: Filter by a particular type of service provider.
          text: |-
            az bot authsetting list-providers --provider-name google
"""


for channel in ['Facebook', 'email', 'Skype', 'Kik', 'Directline', 'Telegram', 'SMS', 'Slack']:
    channel_name = channel.lower()
    helps['bot {0} delete'.format(channel_name)] = """
        type: command
        short-summary: Delete the {0} Channel on a bot
    """.format(channel)
    helps['bot {0} show'.format(channel_name)] = """
        type: command
        short-summary: Get details of the {0} Channel on a bot
    """.format(channel)
    helps['bot {0}'.format(channel_name)] = """
        type: group
        short-summary: Manage the {0} Channel on a bot.
    """.format(channel)


helps['bot msteams delete'] = """
    type: command
    short-summary: Delete the Microsoft Teams Channel on a bot
"""
helps['bot msteams show'] = """
    type: command
    short-summary: Get details of the Microsoft Teams Channel on a bot
"""
helps['bot msteams'] = """
    type: group
    short-summary: Manage the Microsoft Teams Channel on a bot.
"""
helps['bot webchat show'] = """
    type: command
    short-summary: Get details of the Webchat Channel on a bot
"""
helps['bot webchat'] = """
    type: group
    short-summary: Manage the Webchat Channel on a bot.
"""
