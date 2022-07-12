# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .exceptions import AAZUnknownFieldError, AAZUndefinedValueError
from knack.help import _print_indent, REQUIRED_TAG, FIRST_LINE_PREFIX
from knack.util import status_tag_messages

try:
    from knack.preview import _PREVIEW_TAG as PREVIEW_TAG
except ImportError:
    PREVIEW_TAG = '[Preview]'

try:
    from knack.experimental import _EXPERIMENTAL_TAG as EXPERIMENTAL_TAG
except ImportError:
    EXPERIMENTAL_TAG = '[Experimental]'

# pylint: disable=protected-access

shorthand_help_messages = {
    "show-help": 'Try `??` to show more.',
    "short-summary": 'Shorthand syntax supported.',
    "long-summary": 'See https://github.com/Azure/azure-cli/tree/dev/doc/shorthand_syntax.md '
                    'for more about shorthand syntax.'
}


class AAZShowHelp(BaseException):

    def __init__(self, *keys):
        super().__init__()
        self.keys = keys
        self.schema = None

    def show(self):
        from ._arg import AAZObjectArg, AAZDictArg, AAZListArg, AAZBaseArg
        assert self.schema is not None and isinstance(self.schema, AAZBaseArg)
        schema = self.schema
        schema_key = self.keys[0]
        idx = 1
        while idx < len(self.keys):
            key = self.keys[idx]
            if isinstance(schema, AAZObjectArg):
                try:
                    schema = schema[key]
                except AAZUndefinedValueError:
                    # show the help of current schema
                    break
                key = f'.{key}'
            elif isinstance(schema, AAZDictArg):
                try:
                    schema = schema.Element
                except AAZUnknownFieldError:
                    # show the help of current schema
                    break
                key = '{}'
            elif isinstance(schema, AAZListArg):
                try:
                    schema = schema.Element
                except AAZUnknownFieldError:
                    # show the help of current schema
                    break
                key = '[]'
            else:
                # show the help of current schema
                break
            schema_key += key
            idx += 1

        self._print_schema_basic(schema_key, schema)

        if isinstance(schema, AAZObjectArg):
            self._print_object_props_schema(schema, title="Object Properties")
        elif isinstance(schema, AAZDictArg) and isinstance(schema.Element, AAZObjectArg):
            self._print_object_props_schema(schema.Element, title="Dict Element Properties")
        elif isinstance(schema, AAZListArg) and isinstance(schema.Element, AAZObjectArg):
            self._print_object_props_schema(schema.Element, title="List Element Properties")

        _print_indent("")

    @classmethod
    def _print_schema_basic(cls, key, schema):
        indent = 0
        _print_indent('\nArgument', indent)

        help_tags = cls._build_schema_tags(schema, preview=False, experimental=False)
        schema_type = schema._type_in_help
        if help_tags:
            _print_indent(f"{key} {help_tags}{FIRST_LINE_PREFIX}{schema_type}", indent=1)
        else:
            _print_indent(f"{key}{FIRST_LINE_PREFIX}{schema_type}", indent=1)

        short_summary = cls._build_short_summary(schema)
        if short_summary:
            _print_indent(short_summary, indent=2)

        long_summary = cls._build_long_summary(schema)
        if long_summary:
            _print_indent(long_summary, indent=2)

    @classmethod
    def _print_object_props_schema(cls, schema, title):
        LINE_FORMAT = '{name}{padding}{tags}{separator}{short_summary}'

        _print_indent(f"\n{title}")
        layouts = []
        max_header_len = 0

        for prop_schema in schema._fields.values():
            prop_tags = cls._build_schema_tags(prop_schema)
            prop_name = ' '.join(prop_schema._options)

            prop_short_summary = cls._build_short_summary(prop_schema, is_prop=True)

            prop_group_name = prop_schema._arg_group or ""
            header_len = len(prop_name) + len(prop_tags) + (1 if prop_tags else 0)
            if header_len > max_header_len:
                max_header_len = header_len
            layouts.append({
                "name": prop_name,
                "tags": prop_tags,
                'separator': FIRST_LINE_PREFIX if prop_short_summary else '',
                'short_summary': prop_short_summary,
                'group_name': prop_group_name,
                'header_len': header_len
            })

        layouts.sort(key=lambda a: (a['group_name'], 0 if a['tags'] else 1, a['tags'], a['name']))
        for layout in layouts:
            if layout['tags']:
                pad_len = max_header_len - layout['header_len'] + 1
            else:
                pad_len = max_header_len - layout['header_len']
            layout['padding'] = ' ' * pad_len
            _print_indent(
                LINE_FORMAT.format(**layout),
                indent=1,
                subsequent_spaces=max_header_len + 4 + len(FIRST_LINE_PREFIX) - 1
            )

    @staticmethod
    def _build_schema_tags(schema, required=True, preview=True, experimental=False):
        preview = PREVIEW_TAG if preview and schema._is_preview else ''
        experimental = EXPERIMENTAL_TAG if experimental and schema._is_experimental else ''
        required = REQUIRED_TAG if required and schema._required else ''
        tags = ' '.join([x for x in [required, experimental, preview] if x])
        return tags

    @staticmethod
    def _build_short_summary(schema, is_prop=False):
        from ._arg import AAZSimpleTypeArg, AAZCompoundTypeArg
        short_summary = schema._help.get("short-summary", "")

        if isinstance(schema, AAZSimpleTypeArg) and schema.enum:
            choices = schema.enum.to_choices()
            if choices:
                if short_summary:
                    short_summary += '  '
                short_summary += 'Allowed values: {}.'.format(', '.join(sorted([str(x) for x in choices])))
        elif isinstance(schema, AAZCompoundTypeArg):
            if is_prop:
                if short_summary:
                    short_summary += '  '
                short_summary += shorthand_help_messages['show-help']
        return short_summary

    @staticmethod
    def _build_long_summary(schema):
        from ._arg import AAZCompoundTypeArg
        lines = []
        long_summary = schema._help.get("long-summary", "")
        if long_summary:
            lines.append(long_summary)

        if isinstance(schema, AAZCompoundTypeArg):
            lines.append(shorthand_help_messages['long-summary'])

        if schema._is_preview:
            preview = status_tag_messages['preview'].format("This argument")
            lines.append(preview)
        if schema._is_experimental:
            experimental = status_tag_messages['experimental'].format("This argument")
            lines.append(experimental)
        return '\n'.join(lines)
