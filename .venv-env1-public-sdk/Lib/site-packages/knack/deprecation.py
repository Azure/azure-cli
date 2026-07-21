# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import StatusTag, color_map

DEFAULT_DEPRECATED_TAG = '[Deprecated]'
_config_key = 'deprecation'


def resolve_deprecate_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    deprecate_info = None
    try:
        command = _get_command(name)
        deprecate_info = getattr(command, 'deprecate_info', None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            deprecate_info = group_kwargs.get('deprecate_info', None)
    return deprecate_info


# pylint: disable=too-many-instance-attributes
class Deprecated(StatusTag):

    @staticmethod
    def ensure_new_style_deprecation(cli_ctx, kwargs, object_type):
        """ Helper method to make the previous string-based deprecate_info kwarg
            work with the new style. """
        deprecate_info = kwargs.get('deprecate_info', None)
        if isinstance(deprecate_info, Deprecated):
            deprecate_info.object_type = object_type
        elif isinstance(deprecate_info, str):
            deprecate_info = Deprecated(cli_ctx, redirect=deprecate_info, object_type=object_type)
        kwargs['deprecate_info'] = deprecate_info
        return deprecate_info

    def __init__(self, cli_ctx=None, object_type='', target=None, redirect=None, hide=False, expiration=None,
                 tag_func=None, message_func=None, **kwargs):
        """ Create a collection of deprecation metadata.

        :param cli_ctx: The CLI context associated with the deprecated item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object being deprecated.
        :type: object_type: str
        :param target: The name of the object being deprecated.
        :type target: str
        :param redirect: The alternative to redirect users to in lieu of the deprecated item. If omitted it, there is
                         no alternative.
        :type redirect: str
        :param hide: A boolean or CLI version at or above-which the deprecated item will no longer appear
                     in help text, but will continue to work. Warnings will be displayed if the deprecated
                     item is used.
        :type hide: bool OR str
        :param expiration: The CLI version at or above-which the deprecated item will no longer work.
        :type expiration: str
        :param tag_func: Callable which returns the desired unformatted tag string for the deprecated item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the deprecated item.
                             Omit to use the default.
        :type message_func: callable
        """
        def _default_get_message(self):
            msg = "This {} has been deprecated and will be removed ".format(self.object_type)
            if self.expiration:
                msg += "in version '{}'.".format(self.expiration)
            else:
                msg += 'in a future release.'
            if self.redirect:
                msg += " Use '{}' instead.".format(self.redirect)
            return msg

        self.redirect = redirect
        self.hide = hide
        self.expiration = expiration
        self._cli_version = cli_ctx.get_cli_version()

        super().__init__(
            cli_ctx=cli_ctx,
            object_type=object_type,
            target=target,
            color=color_map[_config_key],
            tag_func=tag_func or (lambda _: DEFAULT_DEPRECATED_TAG),
            message_func=message_func or _default_get_message
        )

    def _version_less_than_or_equal_to(self, v1, v2):
        """ Returns true if v1 <= v2. """
        from packaging.version import parse
        return parse(v1) <= parse(v2)

    def expired(self):
        if self.expiration:
            return self._version_less_than_or_equal_to(self.expiration, self._cli_version)
        return False

    def hidden(self):
        hidden = False
        if isinstance(self.hide, bool):
            hidden = self.hide
        elif isinstance(self.hide, str):
            hidden = self._version_less_than_or_equal_to(self.hide, self._cli_version)
        return hidden

    def show_in_help(self):
        return not self.hidden() and not self.expired()


class ImplicitDeprecated(Deprecated):

    def __init__(self, **kwargs):

        def get_implicit_deprecation_message(self):
            msg = "This {} is implicitly deprecated because command group '{}' is deprecated " \
                  "and will be removed ".format(self.object_type, self.target)
            if self.expiration:
                msg += "in version '{}'.".format(self.expiration)
            else:
                msg += 'in a future release.'
            if self.redirect:
                msg += " Use '{}' instead.".format(self.redirect)
            return msg

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_deprecation_message
        })
        super().__init__(**kwargs)
