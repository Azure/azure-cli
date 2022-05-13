# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import get_sdk, ResourceType

from ._client_factory import generic_data_service_factory


class ServiceProperties:
    def __init__(self, cli_ctx, name, service, account_name=None, account_key=None, connection_string=None,
                 sas_token=None):
        self.cli_ctx = cli_ctx
        self.name = name
        self.client = generic_data_service_factory(cli_ctx, service, name=account_name, key=account_key,
                                                   connection_string=connection_string, sas_token=sas_token)
        if not self.client:
            from knack.util import CLIError
            raise CLIError('Failed to initialize data client.')

    def get_service_properties(self):
        return getattr(self.client, 'get_{}_service_properties'.format(self.name))

    def set_service_properties(self):
        return getattr(self.client, 'set_{}_service_properties'.format(self.name))

    def get_logging(self, timeout=None):
        return self.get_service_properties()(timeout=timeout).__dict__['logging']

    def set_logging(self, read, write, delete, retention, timeout=None, version=None):
        t_logging, t_retention_policy = get_sdk(self.cli_ctx, ResourceType.DATA_STORAGE, 'Logging', 'RetentionPolicy',
                                                mod='common.models')

        retention_policy = t_retention_policy(enabled=retention != 0, days=retention)
        logging = t_logging(delete, read, write, retention_policy)
        if version:
            logging.version = str(version)
        return self.set_service_properties()(logging=logging, timeout=timeout)

    def disable_logging(self, timeout=None):
        return self.set_logging(read=False, write=False, delete=False, retention=0, timeout=timeout)

    def get_cors(self, timeout=None):
        return self.get_service_properties()(timeout=timeout).__dict__['cors']

    def add_cors(self, origins, methods, max_age, exposed_headers=None, allowed_headers=None, timeout=None):
        from azure.common import AzureHttpError

        t_cors_rule = get_sdk(self.cli_ctx, ResourceType.DATA_STORAGE, 'CorsRule', mod='common.models')
        cors = self.get_cors(timeout)
        new_rule = t_cors_rule(origins, methods, max_age, exposed_headers, allowed_headers)
        cors.append(new_rule)
        try:
            return self.set_service_properties()(cors=cors, timeout=timeout)
        except AzureHttpError as ex:
            # The service issue: https://msazure.visualstudio.com/DefaultCollection/One/_workitems/edit/1247479.
            # This workaround can be removed once the service is updated.
            if ex.status_code == 400 and len(cors) > 5:
                from knack.util import CLIError
                raise CLIError('Failed to add CORS rules. No more than 5 CORS rule can be added.')

            raise ex

    def clear_cors(self, timeout=None):
        return self.set_service_properties()(cors=[], timeout=timeout)

    def get_metrics(self, interval, timeout=None):
        props = self.get_service_properties()(timeout=timeout)
        metrics = {}
        if interval == 'both':
            metrics['hour'] = props.__dict__['hour_metrics']
            metrics['minute'] = props.__dict__['minute_metrics']
        else:
            metrics[interval] = props.__dict__['{}_metrics'.format(interval)]
        return metrics

    def set_metrics(self, retention, hour, minute, api=None, timeout=None):
        t_metrics, t_retention_policy = get_sdk(self.cli_ctx, ResourceType.DATA_STORAGE, 'Metrics', 'RetentionPolicy',
                                                mod='common.models')

        retention_policy = t_retention_policy(enabled=retention != 0, days=retention)
        hour_metrics = t_metrics(hour, api, retention_policy) if hour is not None else None
        minute_metrics = t_metrics(minute, api, retention_policy) if minute is not None else None
        return self.set_service_properties()(
            hour_metrics=hour_metrics, minute_metrics=minute_metrics, timeout=timeout)