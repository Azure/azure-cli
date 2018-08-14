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
    short-summary: Add azure specific scripts to your local source code directory to 
                   be able to publish back using az bot publish.
"""
helps['bot delete'] = """
    type: command
    short-summary: delete an existing Bot Service.
"""
helps['bot update'] = """
    type: command
    short-summary: update an existing Bot Service.
    examples:
        - name: Update description on a bot
          text: |-
            az bot update -n botName -g MyResourceGroup --set properties.description="some description"
"""
helps['bot publish'] = """
    type: command
    short-summary: publish to an existing Bot Service.
    long-summary: publish your github or zip code to a bot service.
                  This lets you overwrite the existing template code on a bot.
"""
helps['bot download'] = """
    type: command
    short-summary: download an existing Bot Service.
    long-summary: download the code deployed to your web/function app for your bot.
                  You can then make changes to it and publish it back to your app.
"""
helps['bot facebook create'] = """
    type: command
    short-summary: Create Facebook Channel on a Bot.
    examples:
        - name: Add Facebook Channel for a Bot
          text: |-
            az bot facebook create -n botName -g MyResourceGroup -appid myAppId
            --page-d myPageId --secret mySecret --token myToken
"""
helps['bot email create'] = """
    type: command
    short-summary: Create Email Channel on a Bot.
    examples:
        - name: Add Email Channel for a Bot
          text: |-
            az bot email create -n botName -g MyResourceGroup -a abc@outlook.com
            -p password
"""
helps['bot msteams create'] = """
    type: command
    short-summary: Create MsTeams Channel on a Bot.
    examples:
        - name: Add MsTeams Channel for a Bot with calling enabled
          text: |-
            az bot msteams -n botName -g MyResourceGroup --enable-calling
            --calling-web-hook https://www.myapp.com/
"""
helps['bot skype create'] = """
    type: command
    short-summary: Create Skype Channel on a Bot.
    examples:
        - name: Add Skype Channel for a Bot with messaging and screen sharing enabled
          text: |-
            az bot skype -n botName -g MyResourceGroup --enable-messaging
            --enable-screen-sharing
"""
helps['bot kik create'] = """
    type: command
    short-summary: Create Kik Channel on a Bot.
    examples:
        - name: Add Kik Channel for a Bot.
          text: |-
            az bot kik create -n botName -g MyResourceGroup -u mykikname
            -p password --key key --is-validated
"""
helps['bot directline create'] = """
    type: command
    short-summary: Create DirectLine Channel on a Bot with only v3 protocol enabled.
    examples:
        - name: Add DirectLine Channel for a Bot.
          text: |-
            az bot directline create -n botName -g MyResourceGroup --disablev1
"""
helps['bot telegram create'] = """
    type: command
    short-summary: Create Telegram Channel on a Bot.
    examples:
        - name: Add Telegram Channel for a Bot.
          text: |-
            az bot telegram create -n botName -g MyResourceGroup --access-token token
            --is-validated
"""
helps['bot sms create'] = """
    type: command
    short-summary: Create Sms Channel on a Bot.
    examples:
        - name: Add Sms Channel for a Bot.
          text: |-
            az bot sms create -n botName -g MyResourceGroup --account-sid sid
            --auth-token token --is-validated
"""
helps['bot slack create'] = """
    type: command
    short-summary: Create Slack Channel on a Bot.
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
            --client-id clientId --client-secret secret --scopes "scope1 scope2" --service google
            --parameters id=myid
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
        - name: list all service providers.
          text: |-
            az bot authsetting list-providers
        - name: Filter by a particular type of service provider.
          text: |-
            az bot authsetting list-providers --provider-name google
"""

for channel in ['facebook', 'email', 'msteams', 'skype', 'kik', 'webchat', 'directline', 'telegram', 'sms', 'slack']:
    channelTitle = channel[:1].upper() + channel[1:]
    helps['bot {0} delete'.format(channel)] = """
        type: command
        short-summary: Delete {0} Channel on a Bot
    """.format(channelTitle)
    helps['bot {0} show'.format(channel)] = """
        type: command
        short-summary: Get details of {0} Channel on a Bot
    """.format(channelTitle)
    helps['bot {0}'.format(channel)] = """
        type: group
        short-summary: Manage {0} Channel on a Bot.
    """.format(channelTitle)
