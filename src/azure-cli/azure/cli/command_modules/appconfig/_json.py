# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json


DOUBLE_QUOTE = '\"'
BACKSLASH = '\\'
DOUBLE_SLASH = '//'
MULTILINE_COMMENT_START = '/*'
MULTILINE_COMMENT_END = '*/'
NEW_LINE = '\n'


def parse_json_with_comments(json_string):
    try:
        return json.loads(json_string)

    except json.JSONDecodeError:
        return json.loads(__strip_json_comments(json_string))


def __strip_json_comments(json_string):
    current_index = 0
    length = len(json_string)
    result = []

    while current_index < length:
        # Single line comment
        if json_string[current_index:current_index + 2] == DOUBLE_SLASH:
            current_index = __find_next_newline_index(json_string, current_index, length)
            if current_index < length and json_string[current_index] == NEW_LINE:
                result.append(NEW_LINE)

        # Multi-line comment
        elif json_string[current_index:current_index + 2] == MULTILINE_COMMENT_START:
            current_index = __find_next_multiline_comment_end(json_string, current_index + 2, length)

        # String literal
        elif json_string[current_index] == DOUBLE_QUOTE:
            literal_start_index = current_index
            current_index = __find_next_double_quote_index(json_string, current_index + 1, length)

            result.extend(json_string[literal_start_index:current_index + 1])
        else:
            result.append(json_string[current_index])

        current_index += 1

    return "".join(result)


def __is_escaped(json_string, char_index):
    backslash_count = 0
    index = char_index - 1
    while index >= 0 and json_string[index] == BACKSLASH:
        backslash_count += 1
        index -= 1

    return backslash_count % 2 == 1


def __find_next_newline_index(json_string, start_index, end_index):
    index = start_index

    while index < end_index:
        if json_string[index] == NEW_LINE:
            return index

        index += 1

    return index


def __find_next_double_quote_index(json_string, start_index, end_index):
    index = start_index
    while index < end_index:
        if json_string[index] == DOUBLE_QUOTE and not __is_escaped(json_string, index):
            return index

        index += 1

    raise ValueError("Unterminated string literal")


def __find_next_multiline_comment_end(json_string, start_index, end_index):
    index = start_index
    while index < end_index - 1:
        if json_string[index:index + 2] == MULTILINE_COMMENT_END:
            return index + 1

        index += 1

    raise ValueError("Unterminated multi-line comment")
