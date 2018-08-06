# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.commands import LongRunningOperation


def create(client, resource_group_name, account_name, live_event_name, streaming_protocol, location,  # pylint: disable=too-many-locals
           auto_start=False, encoding_type=None, preset_name=None, tags=None, description=None,
           key_frame_interval_duration=None, access_token=None, no_wait=False, ips=None,
           preview_locator=None, streaming_policy_name=None, alternative_media_id=None,
           vanity_url=False, client_access_policy=None, cross_domain_policy=None, stream_options=None):
    from azure.mgmt.media.models import LiveEventInputProtocol
    from azure.mgmt.media.models import LiveEventInput
    from azure.mgmt.media.models import LiveEvent
    from azure.mgmt.media.models import LiveEventEncoding

    live_event_input = LiveEventInput(streaming_protocol=LiveEventInputProtocol(streaming_protocol),
                                      access_token=access_token,
                                      key_frame_interval_duration=key_frame_interval_duration)

    live_event_preview = create_live_event_preview(preview_locator, streaming_policy_name, alternative_media_id,
                                                ips, live_event_name)

    policies = create_cross_site_access_policies(client_access_policy, cross_domain_policy)

    live_event = LiveEvent(input=live_event_input, location=location, preview=live_event_preview,
                           encoding=LiveEventEncoding(encoding_type=encoding_type, preset_name=preset_name),
                           tags=tags, vanity_url=vanity_url, stream_options=stream_options,
                           cross_site_access_policies=policies, description=description)

    return sdk_no_wait(no_wait, client.create, resource_group_name=resource_group_name, account_name=account_name,
                       live_event_name=live_event_name, parameters=live_event, auto_start=auto_start)


def create_live_event_preview(preview_locator, streaming_policy_name, alternative_media_id, ips, live_event_name):
    from azure.mgmt.media.models import LiveEventPreview
    from azure.mgmt.media.models import LiveEventPreviewAccessControl
    from azure.mgmt.media.models import IPAccessControl
    from azure.mgmt.media.models import IPRange

    allow_list = []
    if ips is not None:
        for each in ips:
            allow_list.append(IPRange(name=(live_event_name + each), address=each, subnet_prefix_length=0))

    live_event_preview_access_control = LiveEventPreviewAccessControl(ip=IPAccessControl(allow=allow_list))

    return LiveEventPreview(preview_locator=preview_locator, streaming_policy_name=streaming_policy_name,
                            alternative_media_id=alternative_media_id,
                            access_control=live_event_preview_access_control)


def create_cross_site_access_policies(client_access_policy, cross_domain_policy):
    from azure.mgmt.media.models import CrossSiteAccessPolicies

    with open(client_access_policy, 'r') as file:
        client_policy = file.read()

    with open(cross_domain_policy, 'r') as file:
        domain_policy = file.read()

    return CrossSiteAccessPolicies(client_access_policy=client_policy, cross_domain_policy=domain_policy)


def start(cmd, client, resource_group_name, account_name, live_event_name, no_wait=False):
    if no_wait:
        return sdk_no_wait(no_wait, client.start, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.start(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)


def stop(cmd, client, resource_group_name, account_name, live_event_name,
         remove_outputs_on_stop=False, no_wait=False):

    if no_wait:
        return sdk_no_wait(no_wait, client.stop, resource_group_name, account_name, live_event_name,
                           remove_outputs_on_stop)

    LongRunningOperation(cmd.cli_ctx)(client.stop(resource_group_name, account_name, live_event_name,
                                                  remove_outputs_on_stop))

    return client.get(resource_group_name, account_name, live_event_name)


def reset(cmd, client, resource_group_name, account_name, live_event_name,
          no_wait=False):

    if no_wait:
        return sdk_no_wait(no_wait, client.reset, resource_group_name, account_name, live_event_name)

    LongRunningOperation(cmd.cli_ctx)(client.reset(resource_group_name, account_name, live_event_name))

    return client.get(resource_group_name, account_name, live_event_name)
