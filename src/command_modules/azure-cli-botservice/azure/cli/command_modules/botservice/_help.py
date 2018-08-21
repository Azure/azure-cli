# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['bot'] = """
    type: group
    short-summary: Manage Bot Services.
"""
helps['bot create'] = """
    type: command
    short-summary: Create a new Bot Service.
"""
helps['bot show'] = """
    type: command
    short-summary: Get an existing Bot Service.
"""
helps['bot prepare-publish'] = """
    type: command
    short-summary: Add scripts to your local source code directory to
                   be able to publish back using az bot publish.
"""
helps['bot delete'] = """
    type: command
    short-summary: Delete an existing Bot Service.
"""
helps['bot update'] = """
    type: command
    short-summary: Update an existing Bot Service.
    examples:
        - name: Update description on a bot
          text: |-
            az bot update -n botName -g MyResourceGroup --set properties.description="some description"
"""
helps['bot publish'] = """
    type: command
    short-summary: Publish to an existing Bot Service.
    long-summary: Publish your source code to your Azure Web App.
    examples:
        - name: Publish source code to your Azure App, from within the bot code folder
          text: |-
            az bot publish -n botName -g MyResourceGroup
"""
helps['bot download'] = """
    type: command
    short-summary: Download an existing Bot Service.
    long-summary: The source code is downloaded from the web app associated with the Bot.
                  You can then make changes to it and publish it back to your app.
"""
helps['bot facebook create'] = """
    type: command
    short-summary: Create a Facebook Channel on a Bot.
    examples:
        - name: Create a Facebook Channel for a Bot
          text: |-
            az bot facebook create -n botName -g MyResourceGroup -appid myAppId
            --page-d myPageId --secret mySecret --token myToken
"""
helps['bot email create'] = """
    type: command
    short-summary: Create an Email Channel on a Bot.
    examples:
        - name: Create a Email Channel for a Bot
          text: |-
            az bot email create -n botName -g MyResourceGroup -a abc@outlook.com
            -p password
"""
helps['bot msteams create'] = """
    type: command
    short-summary: Create a Microsoft Teams Channel on a Bot.
    examples:
        - name: Create a Microsoft Teams Channel for a Bot with calling enabled
          text: |-
            az bot msteams create -n botName -g MyResourceGroup --enable-calling
            --calling-web-hook https://www.myapp.com/
"""
helps['bot skype create'] = """
    type: command
    short-summary: Create a Skype Channel on a Bot.
    examples:
        - name: Create a Skype Channel for a Bot with messaging and screen sharing enabled
          text: |-
            az bot skype create -n botName -g MyResourceGroup --enable-messaging
            --enable-screen-sharing
"""
helps['bot kik create'] = """
    type: command
    short-summary: Create a Kik Channel on a Bot.
    examples:
        - name: Create a Kik Channel for a Bot.
          text: |-
            az bot kik create -n botName -g MyResourceGroup -u mykikname
            -p password --key key --is-validated
"""
helps['bot directline create'] = """
    type: command
    short-summary: Create a DirectLine Channel on a Bot with only v3 protocol enabled.
    examples:
        - name: Create a DirectLine Channel for a Bot.
          text: |-
            az bot directline create -n botName -g MyResourceGroup --disablev1
"""
helps['bot telegram create'] = """
    type: command
    short-summary: Create a Telegram Channel on a Bot.
    examples:
        - name: Create a Telegram Channel for a Bot.
          text: |-
            az bot telegram create -n botName -g MyResourceGroup --access-token token
            --is-validated
"""
helps['bot sms create'] = """
    type: command
    short-summary: Create an SMS Channel on a Bot.
    examples:
        - name: Create an SMS Channel for a Bot.
          text: |-
            az bot sms create -n botName -g MyResourceGroup --account-sid sid
            --auth-token token --is-validated
"""
helps['bot slack create'] = """
    type: command
    short-summary: Create a Slack Channel on a Bot.
    examples:
        - name: Create a Slack Channel for a Bot.
          text: |-
            az bot slack create -n botName -g MyResourceGroup --client-id clientid
            --client-secret secret --verification-token token
"""
helps['bot authsetting'] = """
    type: group
    short-summary: Manage OAuth Connection Settings on a Bot.
"""
helps['bot authsetting create'] = """
    type: command
    short-summary: Create an OAuth Connection Setting on a Bot.
    examples:
        - name: Create a new OAuth Connection Setting on a Bot.
          text: |-
            az bot authsetting create -g MyResourceGroup -n botName -c myConnectionName
            --client-id clientId --client-secret secret --scopes scope1 scope2 --service google
            --parameters id=myid --scopes-separator :
"""
helps['bot authsetting show'] = """
    type: command
    short-summary: Show details of an OAuth Connection Setting on a Bot.
"""
helps['bot authsetting list'] = """
    type: command
    short-summary: Show all OAuth Connection Settings on a Bot.
"""
helps['bot authsetting delete'] = """
    type: command
    short-summary: Delete an OAuth Connection Setting on a Bot.
"""
helps['bot authsetting list-providers'] = """
    type: command
    short-summary: List Details of All service Providers available for creating OAuth Connection Settings.
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
        short-summary: Delete the {0} Channel on a Bot
    """.format(channel)
    helps['bot {0} show'.format(channel_name)] = """
        type: command
        short-summary: Get details of the {0} Channel on a Bot
    """.format(channel)
    helps['bot {0}'.format(channel_name)] = """
        type: group
        short-summary: Manage the {0} Channel on a Bot.
    """.format(channel)


helps['bot msteams delete'] = """
    type: command
    short-summary: Delete the Microsoft Teams Channel on a Bot
"""
helps['bot msteams show'] = """
    type: command
    short-summary: Get details of the Microsoft Teams Channel on a Bot
"""
helps['bot msteams'] = """
    type: group
    short-summary: Manage the Microsoft Teams Channel on a Bot.
"""
helps['bot webchat show'] = """
    type: command
    short-summary: Get details of the Webchat Channel on a Bot
"""
helps['bot webchat'] = """
    type: group
    short-summary: Manage the Webchat Channel on a Bot.
"""
