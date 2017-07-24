# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import json
import base64
import binascii

from azure.cli.core._pkg_util import COMPONENT_PREFIX, CLI_PACKAGE_NAME

from knack.log import get_logger
from knack.util import CLIError, to_snake_case
import six

logger = get_logger(__name__)


def handle_exception(ex):
    # For error code, follow guidelines at https://docs.python.org/2/library/sys.html#sys.exit,
    from msrestazure.azure_exceptions import CloudError
    if isinstance(ex, (CLIError, CloudError)):
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else 1
    elif isinstance(ex, KeyboardInterrupt):
        return 1

    logger.exception(ex)
    return 1


def empty_on_404(ex):
    from msrestazure.azure_exceptions import CloudError
    if isinstance(ex, CloudError) and ex.status_code == 404:
        return None
    raise ex


def truncate_text(str_to_shorten, width=70, placeholder=' [...]'):
    if width <= 0:
        raise ValueError('width must be greater than 0.')
    s_len = width - len(placeholder)
    return str_to_shorten[:s_len] + (str_to_shorten[s_len:] and placeholder)


def get_az_version_string(out_file):
    import platform
    from pip import get_installed_distributions
    installed_dists = get_installed_distributions(local_only=True)

    cli_info = None
    for dist in installed_dists:
        if dist.key == CLI_PACKAGE_NAME:
            cli_info = {'name': dist.key, 'version': dist.version}
            break

    version_string = ''
    if cli_info:
        version_string += '{} ({})'.format(cli_info['name'], cli_info['version'])

    component_version_info = sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''),
                                      'version': dist.version}
                                     for dist in installed_dists
                                     if dist.key.startswith(COMPONENT_PREFIX)],
                                    key=lambda x: x['name'])

    for c in component_version_info:
        version_string += '\n{} ({})'.format(c['name'], c['version'])

    return version_string


def get_json_object(json_string):
    """ Loads a JSON string as an object and converts all keys to snake case """

    def _convert_to_snake_case(item):
        if isinstance(item, dict):
            new_item = {}
            for key, val in item.items():
                new_item[to_snake_case(key)] = _convert_to_snake_case(val)
            return new_item
        if isinstance(item, list):
            return [_convert_to_snake_case(x) for x in item]
        return item

    return _convert_to_snake_case(shell_safe_json_parse(json_string))


def get_file_json(file_path, throw_on_empty=True, preserve_order=False):
    content = read_file_content(file_path)
    if not content and not throw_on_empty:
        return None
    return shell_safe_json_parse(content, preserve_order)


def read_file_content(file_path, allow_binary=False):
    from codecs import open as codecs_open
    # Note, always put 'utf-8-sig' first, so that BOM in WinOS won't cause trouble.
    for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be']:
        try:
            with codecs_open(file_path, encoding=encoding) as f:
                logger.debug("attempting to read file %s as %s", file_path, encoding)
                return f.read()
        except UnicodeDecodeError:
            if allow_binary:
                with open(file_path, 'rb') as input_file:
                    logger.debug("attempting to read file %s as binary", file_path)
                    return base64.b64encode(input_file.read()).decode("utf-8")
            else:
                raise
        except UnicodeError:
            pass

    raise CLIError('Failed to decode file {} - unknown decoding'.format(file_path))


def shell_safe_json_parse(json_or_dict_string, preserve_order=False):
    """ Allows the passing of JSON or Python dictionary strings. This is needed because certain
    JSON strings in CMD shell are not received in main's argv. This allows the user to specify
    the alternative notation, which does not have this problem (but is technically not JSON). """
    try:
        if not preserve_order:
            return json.loads(json_or_dict_string)
        from collections import OrderedDict
        return json.loads(json_or_dict_string, object_pairs_hook=OrderedDict)
    except ValueError as json_ex:
        try:
            import ast
            return ast.literal_eval(json_or_dict_string)
        except SyntaxError:
            raise CLIError(json_ex)


def b64encode(s):
    """
    Encodes a string to base64 on 2.x and 3.x
    :param str s: latin_1 encoded string
    :return: base64 encoded string
    :rtype: str
    """
    encoded = base64.b64encode(six.b(s))
    return encoded if encoded is str else encoded.decode('latin-1')


def b64_to_hex(s):
    """
    Decodes a string to base64 on 2.x and 3.x
    :param str s: base64 encoded string
    :return: uppercase hex string
    :rtype: str
    """
    decoded = base64.b64decode(s)
    hex_data = binascii.hexlify(decoded).upper()
    if isinstance(hex_data, bytes):
        return str(hex_data.decode("utf-8"))
    return hex_data


def random_string(length=16, force_lower=False, digits_only=False):
    from string import ascii_letters, digits, ascii_lowercase
    from random import choice
    choice_set = digits
    if not digits_only:
        choice_set += ascii_lowercase if force_lower else ascii_letters
    return ''.join([choice(choice_set) for _ in range(length)])


def hash_string(value, length=16, force_lower=False):
    """ Generate a deterministic hashed string."""
    import hashlib
    m = hashlib.sha256()
    try:
        m.update(value)
    except TypeError:
        m.update(value.encode())
    digest = m.hexdigest()
    digest = digest.lower() if force_lower else digest
    while len(digest) < length:
        digest = digest + digest
    return digest[:length]
