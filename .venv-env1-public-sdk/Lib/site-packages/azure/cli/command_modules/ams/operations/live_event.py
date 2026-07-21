# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import CLIError, sdk_no_wait

from azure.cli.command_modules.ams._utils import (create_ip_range, show_resource_not_found_message)
from azure.mgmt.media.models import (CrossSiteAccessPolicies, IPAccessControl, LiveEvent,
                                     LiveEventEncoding, LiveEventInput, LiveEventInputAccessControl,
                                     LiveEventInputProtocol, LiveEventPreview, LiveEventPreviewAccessControl,
                                     LiveEventActionInput)


def create(cmd, client, resource_group_name, account_name, live_event_name, streaming_protocol, ips,  # pylint: disable=too-many-locals
           auto_start=False, encoding_type=None, preset_name=None, stretch_mode=None, key_frame_interval=None,
           tags=None, description=None, key_frame_interval_duration=None, access_token=None, no_wait=False,
           preview_ips=None, preview_locator=None, streaming_policy_name=None, alternative_media_id=None,
           client_access_policy=None, cross_domain_policy=None, stream_options=None,
           transcription_lang=None, use_static_hostname=False, hostname_prefix=None):

    from azure.cli.command_modules.ams._client_factory import (get_mediaservices_client)

    allowed_ips = []
    if ips[0] == 'AllowAll':
        ips = ['0.0.0.0/0']
    for ip in ips:
        allowed_ips.append(create_ip_range(live_event_name, ip))

    live_event_input_access_control = LiveEventInputAccessControl(ip=IPAccessControl(allow=allowed_ips))

    transcriptions = []
    if transcription_lang:
        transcriptions = [{'language': transcription_lang}]

    live_event_input = LiveEventInput(streaming_protocol=LiveEventInputProtocol(streaming_protocol),
                                      access_token=access_token,
                                      key_frame_interval_duration=key_frame_interval_duration,
                                      access_control=live_event_input_access_control)

    ams_client = get_mediaservices_client(cmd.cli_ctx)
    ams = ams_client.get(resource_group_name, account_name)
    location = ams.location

    live_event_preview = create_live_event_preview(preview_locator, streaming_policy_name, alternative_media_id,
                                                   preview_ips, live_event_name)

    policies = create_cross_site_access_policies(client_access_policy, cross_domain_policy)

    live_event = LiveEvent(input=live_event_input, location=location, preview=live_event_preview,
                           encoding=LiveEventEncoding(encoding_type=encoding_type, preset_name=preset_name,
                                                      stretch_mode=stretch_mode, key_frame_interval=key_frame_interval),
                           tags=tags, stream_options=stream_options, cross_site_access_policies=policies,
                           description=description, transcriptions=transcriptions,
                           use_static_hostname=use_static_hostname, hostname_prefix=hostname_prefix, system_data=None)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name=resource_group_name, account_name=account_name,
                       live_event_name=live_event_name, parameters=live_event, auto_start=auto_start)


def create_live_event_preview(preview_locator, streaming_policy_name,
                              alternative_media_id, preview_ips, live_event_name):

    allow_list = []
    if preview_ips is None:
        preview_ips = []
    if preview_ips != [] and preview_ips[0] == 'AllowAll':
        preview_ips = ['0.0.0.0/0']

    for ip in preview_ips:
        allow_list.append(create_ip_range(live_event_name, ip))

    live_event_preview_access_control = LiveEventPreviewAccessControl(ip=IPAccessControl(allow=allow_list))

    return LiveEventPreview(preview_locator=preview_locator, streaming_policy_name=streaming_policy_name,
                            alternative_media_id=alternative_media_id,
                            access_control=live_event_preview_access_control)


def create_cross_site_access_policies(client_access_policy, cross_domain_policy):

    policies = CrossSiteAccessPolicies()

    if client_access_policy:
        policies.client_access_policy = client_access_policy

    if cross_domain_policy:
        policies.cross_domain_policy = cross_domain_policy

    return policies


def start(cmd, client, resource_group_name, account_name, live_event_name, no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.begin_start, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.begin_start(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)


def standby(cmd, client, resource_group_name, account_name, live_event_name, no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.begin_allocate, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.begin_allocate(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)


def stop(cmd, client, resource_group_name, account_name, live_event_name,
         remove_outputs_on_stop=False, no_wait=False):

    if no_wait:
        return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, account_name, live_event_name,
                           remove_outputs_on_stop)

    parameters = LiveEventActionInput(remove_outputs_on_stop=remove_outputs_on_stop)
    LongRunningOperation(cmd.cli_ctx)(client.begin_stop(resource_group_name, account_name, live_event_name,
                                                        parameters))

    return client.get(resource_group_name, account_name, live_event_name)


def reset(cmd, client, resource_group_name, account_name, live_event_name,
          no_wait=False):

    if no_wait:
        return sdk_no_wait(no_wait, client.begin_reset, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.begin_reset(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)


def update_live_event_setter(client, resource_group_name, account_name, live_event_name,
                             parameters):
    ips = list(map(lambda x: create_ip_range(live_event_name, x) if isinstance(x, str) else x,
                   parameters.input.access_control.ip.allow))
    preview_ips = list(map(lambda x: create_ip_range(live_event_name, x) if isinstance(x, str) else x,
                           parameters.preview.access_control.ip.allow))
    parameters.input.access_control.ip.allow = ips
    parameters.preview.access_control.ip.allow = preview_ips
    return client.begin_update(resource_group_name, account_name, live_event_name, parameters)


def update_live_event(instance, tags=None, description=None, key_frame_interval_duration=None,
                      preview_ips=None, ips=None, client_access_policy=None, cross_domain_policy=None):
    if not instance:
        raise CLIError('The live event resource was not found.')

    if tags is not None:
        instance.tags = tags

    if description is not None:
        instance.description = description

    if key_frame_interval_duration is not None:
        instance.input.key_frame_interval_duration = key_frame_interval_duration

    if preview_ips is not None:
        instance.preview.access_control.ip.allow = []
        if len(preview_ips) > 1 or preview_ips[0]:
            if preview_ips[0] == 'AllowAll':
                preview_ips = ['0.0.0.0/0']
            for ip in preview_ips:
                instance.preview.access_control.ip.allow.append(create_ip_range(instance.name, ip))

    if ips is not None:
        instance.input.access_control.ip.allow = []
        if len(ips) > 1 or ips[0]:
            if ips[0] == 'AllowAll':
                ips = ['0.0.0.0/0']
            for ip in ips:
                instance.input.access_control.ip.allow.append(create_ip_range(instance.name, ip))

    if client_access_policy is not None:
        if not client_access_policy:
            instance.cross_site_access_policies.client_access_policy = None
        else:
            instance.cross_site_access_policies.client_access_policy = client_access_policy

    if cross_domain_policy is not None:
        if not cross_domain_policy:
            instance.cross_site_access_policies.cross_domain_policy = None
        else:
            instance.cross_site_access_policies.cross_domain_policy = cross_domain_policy

    return instance


def get_live_event(client, resource_group_name, account_name, live_event_name):
    live_event = client.get(resource_group_name, account_name, live_event_name)
    if not live_event:
        show_resource_not_found_message(
            resource_group_name, account_name, 'liveEvents', live_event_name)

    return live_event
