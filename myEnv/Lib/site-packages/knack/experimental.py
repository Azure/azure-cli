# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import StatusTag

_EXPERIMENTAL_TAG = '[Experimental]'
_experimental_kwarg = 'experimental_info'


def resolve_experimental_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    experimental_info = None
    try:
        command = _get_command(name)
        experimental_info = getattr(command, _experimental_kwarg, None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            experimental_info = group_kwargs.get(_experimental_kwarg, None)
    return experimental_info


# pylint: disable=too-many-instance-attributes
class ExperimentalItem(StatusTag):

    def __init__(self, cli_ctx, object_type='', target=None, tag_func=None, message_func=None, **kwargs):
        """ Create a collection of experimental metadata.

        :param cli_ctx: The CLI context associated with the experimental item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object in experimental.
        :type: object_type: str
        :param target: The name of the object in experimental.
        :type target: str
        :param tag_func: Callable which returns the desired unformatted tag string for the experimental item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the experimental item.
                             Omit to use the default.
        :type message_func: callable
        """

        def _default_get_message(self):
            return "This {} is experimental and not covered by customer support. " \
                   "Please use with discretion.".format(self.object_type)

        super(ExperimentalItem, self).__init__(
            cli_ctx=cli_ctx,
            object_type=object_type,
            target=target,
            color='cyan',
            tag_func=tag_func or (lambda _: _EXPERIMENTAL_TAG),
            message_func=message_func or _default_get_message
        )


class ImplicitExperimentalItem(ExperimentalItem):

    def __init__(self, **kwargs):

        def get_implicit_experimental_message(self):
            return "Command group '{}' is experimental and not covered by customer support. " \
                   "Please use with discretion.".format(self.target)

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_experimental_message
        })
        super(ImplicitExperimentalItem, self).__init__(**kwargs)
