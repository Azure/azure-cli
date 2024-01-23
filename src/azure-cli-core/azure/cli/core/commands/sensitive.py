# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import StatusTag

_SENSITIVE_TAG = '[Sensitive]'
_sensitive_kwarg = 'sensitive_info'
_config_key = 'sensitive'


def resolve_sensitive_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    sensitive_info = None
    try:
        command = _get_command(name)
        sensitive_info = getattr(command, _sensitive_kwarg, None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            sensitive_info = group_kwargs.get(_sensitive_kwarg, None)
    return sensitive_info


# pylint: disable=too-many-instance-attributes
class SensitiveItem(StatusTag):

    def __init__(self, cli_ctx, object_type='', redact=True, sensitive_keys=None,
                 target=None, tag_func=None, message_func=None, **kwargs):
        """ Create a collection of sensitive metadata.

        :param cli_ctx: The CLI context associated with the sensitive item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object containing sensitive info.
        :type: object_type: str
        :param redact: Whether or not to redact the sensitive information.
        :type redact: bool
        :param target: The name of the object containing sensitive info.
        :type target: str
        :param tag_func: Callable which returns the desired unformatted tag string for the sensitive item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the sensitive item.
                             Omit to use the default.
        :type message_func: callable
        """

        def _default_get_message(self):
            from ..credential_helper import sensitive_data_detailed_warning_message, sensitive_data_warning_message
            if self.sensitive_keys:
                return sensitive_data_detailed_warning_message.format(', '.join(self.sensitive_keys))
            return sensitive_data_warning_message

        super().__init__(
            cli_ctx=cli_ctx,
            object_type=object_type,
            target=target,
            color='\x1b[33m',
            tag_func=tag_func or (lambda _: _SENSITIVE_TAG),
            message_func=message_func or _default_get_message
        )
        self.redact = redact
        self.sensitive_keys = sensitive_keys if sensitive_keys else []


class ImplicitSensitiveItem(SensitiveItem):

    def __init__(self, **kwargs):

        def get_implicit_experimental_message(self):
            return "{} may contain sensitive data, please take care.".format("Command group '{}'".format(self.target))

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_experimental_message
        })
        super().__init__(**kwargs)
