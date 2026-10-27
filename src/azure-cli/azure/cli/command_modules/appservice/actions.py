# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from knack.util import CLIError

# pylint:disable=protected-access, too-few-public-methods


class KeyValueAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parsed_pairs = {}
        for item in values:
            try:
                key, value = item.split('=', 1)
                parsed_pairs[key] = value
            except ValueError:
                raise CLIError(
                    'usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))

        # Apply any key remapping defined by subclasses
        result = self._remap_key_value_pairs(parsed_pairs)

        # Accumulate results in a list on the namespace
        if not hasattr(namespace, self.dest) or namespace.__dict__[self.dest] is None:
            namespace.__dict__[self.dest] = []
        namespace.__dict__[self.dest].append(result)

        return result

    def _remap_key_value_pairs(self, parsed_pairs):
        """Override this method in subclasses to remap key value pairs as needed."""
        return parsed_pairs


class RegistryAdapterAddAction(KeyValueAddAction):
    def _remap_key_value_pairs(self, parsed_pairs):
        """Remap key value pairs to match the expected registry adapter structure."""
        result = {}

        for key, value in parsed_pairs.items():
            if key == 'registry-key':
                result['registryKey'] = value
            elif key == 'type':
                result['type'] = value
            elif key == 'secret-uri':
                result['keyVaultSecretReference'] = {'secretUri': value}
            else:
                continue  # Ignore unknown keys or handle as needed

        return result


class StorageMountAddAction(KeyValueAddAction):
    def _remap_key_value_pairs(self, parsed_pairs):
        """Remap key value pairs to match the expected storage mount structure."""
        result = {}

        for key, value in parsed_pairs.items():
            if key == 'name':
                result['name'] = value
            elif key == 'source':
                result['source'] = value
            elif key == 'type':
                result['type'] = value
            elif key == 'destination-path':
                result['destinationPath'] = value
            elif key == 'credentials-secret-uri':
                result['credentialsKeyVaultReference'] = {'secretUri': value}
            else:
                continue  # Ignore unknown keys or handle as needed

        return result


class InstallScriptAddAction(KeyValueAddAction):
    def _remap_key_value_pairs(self, parsed_pairs):
        """Remap key value pairs to match the expected install script structure."""
        result = {}
        source = {}

        for key, value in parsed_pairs.items():
            if key == 'name':
                result['name'] = value
            elif key == 'source-uri':
                source['sourceUri'] = value
            elif key == 'type':
                source['type'] = value
            else:
                continue  # Ignore unknown keys or handle as needed

        # Only add source if it has content
        if source:
            result['source'] = source

        return result
