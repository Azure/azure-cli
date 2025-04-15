# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType, get_sdk


class ServiceProperties:
    name_to_resource = {'blob': ResourceType.DATA_STORAGE_BLOB,
                        'file': ResourceType.DATA_STORAGE_FILESHARE,
                        'queue': ResourceType.DATA_STORAGE_QUEUE,
                        'table': ResourceType.DATA_STORAGE_TABLE}

    def __init__(self, cli_ctx, name, client):
        self.cli_ctx = cli_ctx
        self.name = name
        self.client = client

    @staticmethod
    def table_cors_to_generated(i):
        i.allowed_origins = ",".join(i.allowed_origins)
        i.allowed_methods = ",".join(i.allowed_methods)
        i.allowed_headers = ",".join(i.allowed_headers)
        i.exposed_headers = ",".join(i.exposed_headers)
        return i

    def get_cors(self, timeout=None, to_string=False):
        """ In blob, file, queue service, CorsRule's `allowed_origins`, `allowed_methods`, `allowed_headers` and
        `exposed_headers` are string, but in TableCorsRule, they become list.
        If `to_string` is True, convert TableCorsRule's properties to string.
        """
        r = self.client.get_service_properties(timeout=timeout)['cors']
        if not to_string:
            return r

        if self.name == 'table':
            r = [self.table_cors_to_generated(i) for i in r]

        for i in r:
            # backwards compatibility when migrate multiapi to Track 2
            i.allowed_origins = i.allowed_origins.replace(',', ', ')
            i.allowed_methods = i.allowed_methods.replace(',', ', ')
            i.allowed_headers = i.allowed_headers.replace(',', ', ')
            i.exposed_headers = i.exposed_headers.replace(',', ', ')
        return r

    def add_cors(self, origins, methods, max_age, exposed_headers=None, allowed_headers=None, timeout=None):
        from azure.core.exceptions import HttpResponseError

        exposed_headers = [] if exposed_headers is None else exposed_headers
        allowed_headers = [] if allowed_headers is None else allowed_headers

        if self.name == 'table':
            from azure.data.tables import TableCorsRule
            t_cors_rule = TableCorsRule
        else:
            t_cors_rule = get_sdk(self.cli_ctx, self.name_to_resource[self.name], '#CorsRule')
        cors = self.get_cors(timeout)
        new_rule = t_cors_rule(origins, methods, max_age_in_seconds=max_age, exposed_headers=exposed_headers,
                               allowed_headers=allowed_headers)
        cors.append(new_rule)

        try:
            return self.client.set_service_properties(cors=cors, timeout=timeout)
        except HttpResponseError as ex:
            # The service issue: https://msazure.visualstudio.com/DefaultCollection/One/_workitems/edit/1247479.
            # This workaround can be removed once the service is updated.
            if ex.status_code == 400 and len(cors) > 5:
                from knack.util import CLIError
                raise CLIError('Failed to add CORS rules. No more than 5 CORS rules can be added.')

            raise ex

    def clear_cors(self, timeout=None):
        return self.client.set_service_properties(cors=[], timeout=timeout)

    def get_logging(self, timeout=None):
        return self.client.get_service_properties(timeout=timeout)['analytics_logging']

    @staticmethod
    def create_retention_policy(t_retention_policy, retention):
        return t_retention_policy(enabled=True, days=retention) if retention else t_retention_policy(enabled=False)

    def set_logging(self, read, write, delete, retention, timeout=None, version=None):
        if self.name == 'table':
            from azure.data.tables import TableAnalyticsLogging, TableRetentionPolicy
            t_logging = TableAnalyticsLogging
            t_retention_policy = TableRetentionPolicy
        else:
            logging_class = '#{}AnalyticsLogging'.format(self.name.capitalize())
            t_logging, t_retention_policy = get_sdk(self.cli_ctx, self.name_to_resource[self.name], logging_class,
                                                    '#RetentionPolicy')

        retention_policy = self.create_retention_policy(t_retention_policy, retention)
        logging = t_logging(delete=delete, read=read, write=write, retention_policy=retention_policy)
        if version:
            logging.version = str(version)
        return self.client.set_service_properties(analytics_logging=logging, timeout=timeout)

    def disable_logging(self, timeout=None):
        return self.set_logging(read=False, write=False, delete=False, retention=0, timeout=timeout)

    def get_metrics(self, interval, timeout=None):
        props = self.client.get_service_properties(timeout=timeout)
        metrics = {}
        if interval == 'both':
            metrics['hour'] = props['hour_metrics']
            metrics['minute'] = props['minute_metrics']
        else:
            metrics[interval] = props['{}_metrics'.format(interval)]
        return metrics

    @staticmethod
    def create_metrics(t_metrics, enabled, api, retention_policy):
        kwargs = {'enabled': enabled, 'include_apis': api, 'retention_policy': retention_policy}
        if not enabled:
            kwargs.pop('include_apis')
        return t_metrics(**kwargs)

    def set_metrics(self, retention, hour, minute, api=None, timeout=None):
        if self.name == 'table':
            from azure.data.tables import TableMetrics, TableRetentionPolicy
            t_metrics = TableMetrics
            t_retention_policy = TableRetentionPolicy
        else:
            t_metrics, t_retention_policy = get_sdk(self.cli_ctx, self.name_to_resource[self.name], '#Metrics',
                                                    '#RetentionPolicy')

        retention_policy = self.create_retention_policy(t_retention_policy, retention)

        # Hour and minute can't be None because of `process_metric_update_namespace`, so the property of hour_metrics
        # and minute_metrics changes together.
        hour_metrics = self.create_metrics(t_metrics, hour, api, retention_policy) if hour is not None else None
        minute_metrics = self.create_metrics(t_metrics, minute, api, retention_policy) if minute is not None else None

        return self.client.set_service_properties(
            hour_metrics=hour_metrics, minute_metrics=minute_metrics, timeout=timeout)
