# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access

import argparse
from collections import defaultdict
from knack.util import CLIError


class AddFilters(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'operand':
                d['operand'] = v[0]
            elif kl == 'operator':
                d['operator'] = v[0]
            elif kl == 'values':
                d['values'] = v
        return d


class AddOrderBy(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'order-by':
                d['order_by'] = v[0]
            elif kl == 'order':
                d['order'] = v[0]
        return d


class AddSku(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.sku = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]

            if kl == 'name':
                d['name'] = v[0]

            elif kl == 'capacity':
                d['capacity'] = v[0]

            elif kl == 'size':
                d['size'] = v[0]

            else:
                raise CLIError(
                    'Unsupported Key {} is provided for parameter sku. All possible keys are: name, capacity, size'
                    .format(k)
                )

        return d


class AddOptimizedAutoscale(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.optimized_autoscale = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]

            if kl == 'version':
                d['version'] = v[0]

            elif kl == 'is-enabled':
                d['is_enabled'] = v[0]

            elif kl == 'minimum':
                d['minimum'] = v[0]

            elif kl == 'maximum':
                d['maximum'] = v[0]

            else:
                raise CLIError(
                    'Unsupported Key {} is provided for parameter optimized-autoscale. All possible keys are: version,'
                    ' is-enabled, minimum, maximum'.format(k)
                )

        return d


class AddValue(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]

            if kl == 'language-extension-name':
                d['language_extension_name'] = v[0]

            else:
                raise CLIError(
                    'Unsupported Key {} is provided for parameter value. All possible keys are: language-extension-name'
                    .format(k)
                )

        return d


class AddTableLevelSharingProperties(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.table_level_sharing_properties = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]

            if kl == 'tables-to-include':
                d['tables_to_include'] = v

            elif kl == 'tables-to-exclude':
                d['tables_to_exclude'] = v

            elif kl == 'external-tables-to-include':
                d['external_tables_to_include'] = v

            elif kl == 'external-tables-to-exclude':
                d['external_tables_to_exclude'] = v

            elif kl == 'materialized-views-to-include':
                d['materialized_views_to_include'] = v

            elif kl == 'materialized-views-to-exclude':
                d['materialized_views_to_exclude'] = v

            else:
                raise CLIError(
                    'Unsupported Key {} is provided for parameter table-level-sharing-properties. All possible keys'
                    ' are: tables-to-include, tables-to-exclude, external-tables-to-include,'
                    ' external-tables-to-exclude, materialized-views-to-include, materialized-views-to-exclude'.format(
                        k
                    )
                )

        return d


class AddReadWriteDatabase(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.read_write_database = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]

            if kl == 'soft-delete-period':
                d['soft_delete_period'] = v[0]

            elif kl == 'hot-cache-period':
                d['hot_cache_period'] = v[0]

            elif kl == 'location':
                d['location'] = v[0]

            else:
                raise CLIError(
                    'Unsupported Key {} is provided for parameter read-write-database. All possible keys are:'
                    ' soft-delete-period, hot-cache-period, location'.format(k)
                )

        d['kind'] = 'ReadWrite'

        return d
