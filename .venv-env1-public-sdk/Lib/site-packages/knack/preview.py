# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import StatusTag, status_tag_messages, color_map

_PREVIEW_TAG = '[Preview]'
_preview_kwarg = 'preview_info'
_config_key = 'preview'


def resolve_preview_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    preview_info = None
    try:
        command = _get_command(name)
        preview_info = getattr(command, _preview_kwarg, None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            preview_info = group_kwargs.get(_preview_kwarg, None)
    return preview_info


# pylint: disable=too-many-instance-attributes
class PreviewItem(StatusTag):

    def __init__(self, cli_ctx, object_type='', target=None, tag_func=None, message_func=None, **kwargs):
        """ Create a collection of preview metadata.

        :param cli_ctx: The CLI context associated with the preview item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object in preview.
        :type: object_type: str
        :param target: The name of the object in preview.
        :type target: str
        :param tag_func: Callable which returns the desired unformatted tag string for the preview item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the preview item.
                             Omit to use the default.
        :type message_func: callable
        """

        def _default_get_message(self):
            return status_tag_messages[_config_key].format("This " + self.object_type)

        super().__init__(
            cli_ctx=cli_ctx,
            object_type=object_type,
            target=target,
            color=color_map[_config_key],
            tag_func=tag_func or (lambda _: _PREVIEW_TAG),
            message_func=message_func or _default_get_message
        )


class ImplicitPreviewItem(PreviewItem):

    def __init__(self, **kwargs):

        def get_implicit_preview_message(self):
            return status_tag_messages[_config_key].format("Command group '{}'".format(self.target))

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_preview_message
        })
        super().__init__(**kwargs)
