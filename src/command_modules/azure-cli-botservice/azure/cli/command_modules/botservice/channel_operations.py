# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.botservice.models import BotChannel


def create_channel(client, channel, channel_name, resource_group_name, resource_name):
    botChannel = BotChannel(
        location='global',
        properties=channel
    )
    return client.create(
        resource_group_name=resource_group_name,
        resource_name=resource_name,
        channel_name=channel_name,
        parameters=botChannel
    )


def facebook_create(client, resource_group_name, resource_name, page_id, app_id, app_secret, access_token, is_disabled=None):  # pylint: disable=line-too-long
    from azure.mgmt.botservice.models import FacebookChannel, FacebookChannelProperties, FacebookPage
    channel = FacebookChannel(
        properties=FacebookChannelProperties(
            pages=[FacebookPage(id=page_id, access_token=access_token)],
            app_id=app_id,
            app_secret=app_secret,
            is_enabled=not is_disabled
        )
    )
    return create_channel(client, channel, 'FacebookChannel', resource_group_name, resource_name)


def email_create(client, resource_group_name, resource_name, email_address, password, is_disabled=None):
    from azure.mgmt.botservice.models import EmailChannel, EmailChannelProperties
    channel = EmailChannel(
        properties=EmailChannelProperties(
            email_address=email_address,
            password=password,
            is_enabled=not is_disabled
        )
    )
    return create_channel(client, channel, 'EmailChannel', resource_group_name, resource_name)


def msteams_create(client, resource_group_name, resource_name, is_disabled=None,
                   enable_calling=None, calling_web_hook=None):
    from azure.mgmt.botservice.models import MsTeamsChannel, MsTeamsChannelProperties
    channel = MsTeamsChannel(
        properties=MsTeamsChannelProperties(
            is_enabled=not is_disabled,
            enable_calling=enable_calling,
            calling_web_hook=calling_web_hook
        )
    )
    return create_channel(client, channel, 'MsTeamsChannel', resource_group_name, resource_name)


def skype_create(client, resource_group_name, resource_name, is_disabled=None, enable_messaging=None,
                 enable_media_cards=None, enable_video=None, enable_calling=None,
                 enable_screen_sharing=None, enable_groups=None, groups_mode=None, calling_web_hook=None):
    from azure.mgmt.botservice.models import SkypeChannel, SkypeChannelProperties
    channel = SkypeChannel(
        properties=SkypeChannelProperties(
            is_enabled=not is_disabled,
            enable_messaging=enable_messaging,
            enable_media_cards=enable_media_cards,
            enable_video=enable_video,
            enable_calling=enable_calling,
            enable_screen_sharing=enable_screen_sharing,
            enable_groups=enable_groups,
            groups_mode=groups_mode,
            calling_web_hook=calling_web_hook
        )
    )
    return create_channel(client, channel, 'SkypeChannel', resource_group_name, resource_name)


def kik_create(client, resource_group_name, resource_name, user_name, api_key, is_disabled=None, is_validated=None):
    from azure.mgmt.botservice.models import KikChannel, KikChannelProperties
    channel = KikChannel(
        properties=KikChannelProperties(
            user_name=user_name,
            api_key=api_key,
            is_enabled=not is_disabled,
            is_validated=is_validated
        )
    )
    return create_channel(client, channel, 'KikChannel', resource_group_name, resource_name)


def directline_create(client, resource_group_name, resource_name, is_disabled=None,
                      is_v1_disabled=None, is_v3_disabled=None, site_name='Default Site'):
    from azure.mgmt.botservice.models import DirectLineChannel, DirectLineChannelProperties, DirectLineSite
    channel = DirectLineChannel(
        properties=DirectLineChannelProperties(
            sites=[DirectLineSite(
                site_name=site_name,
                is_enabled=not is_disabled,
                is_v1_enabled=not is_v1_disabled,
                is_v3_enabled=not is_v3_disabled
            )]
        )
    )
    return create_channel(client, channel, 'DirectLineChannel', resource_group_name, resource_name)


def telegram_create(client, resource_group_name, resource_name, access_token, is_disabled=None, is_validated=None):
    from azure.mgmt.botservice.models import TelegramChannel, TelegramChannelProperties
    channel = TelegramChannel(
        properties=TelegramChannelProperties(
            access_token=access_token,
            is_enabled=not is_disabled,
            is_validated=is_validated
        )
    )
    return create_channel(client, channel, 'TelegramChannel', resource_group_name, resource_name)


def sms_create(client, resource_group_name, resource_name, phone, account_sid, auth_token, is_disabled=None, is_validated=None):  # pylint: disable=line-too-long
    from azure.mgmt.botservice.models import SmsChannel, SmsChannelProperties
    channel = SmsChannel(
        properties=SmsChannelProperties(
            phone=phone,
            account_sid=account_sid,
            auth_token=auth_token,
            is_enabled=not is_disabled,
            is_validated=is_validated
        )
    )
    return create_channel(client, channel, 'SmsChannel', resource_group_name, resource_name)


def slack_create(client, resource_group_name, resource_name, client_id, client_secret, verification_token,
                 is_disabled=None, landing_page_url=None):
    from azure.mgmt.botservice.models import SlackChannel, SlackChannelProperties
    channel = SlackChannel(
        properties=SlackChannelProperties(
            client_id=client_id,
            client_secret=client_secret,
            verification_token=verification_token,
            landing_page_url=landing_page_url,
            is_enabled=not is_disabled
        )
    )
    return create_channel(client, channel, 'SlackChannel', resource_group_name, resource_name)


class ChannelOperations(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        for channel in ['facebook', 'email', 'msTeams', 'skype', 'kik', 'webChat', 'directLine', 'telegram', 'sms', 'slack']:  # pylint: disable=line-too-long
            channelName = '{}Channel'.format(channel)
            channelName = channelName[:1].upper() + channelName[1:]

            def get_wrapper(channel_name):
                def get(client, resource_group_name, resource_name, show_secrets=None):
                    if show_secrets:
                        return client.list_with_keys(
                            resource_group_name=resource_group_name,
                            resource_name=resource_name,
                            channel_name=channel_name,
                        )
                    return client.get(
                        resource_group_name=resource_group_name,
                        resource_name=resource_name,
                        channel_name=channel_name
                    )
                return get

            def delete_wrapper(channel_name):
                def delete(client, resource_group_name, resource_name):
                    return client.delete(
                        resource_group_name=resource_group_name,
                        resource_name=resource_name,
                        channel_name=channel_name
                    )
                return delete
            setattr(self, '{}_get'.format(channel.lower()), get_wrapper(channelName))
            setattr(self, '{}_delete'.format(channel.lower()), delete_wrapper(channelName))


channelOperationsInstance = ChannelOperations()
