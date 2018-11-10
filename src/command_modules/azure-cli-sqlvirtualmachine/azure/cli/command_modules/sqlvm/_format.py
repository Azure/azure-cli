# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation


def _last_segment(resource_id):
    return resource_id.split('/')[-1] if resource_id else None


_units = [(1024 * 1024 * 1024 * 1024, 'TB'),
          (1024 * 1024 * 1024, 'GB'),
          (1024 * 1024, 'MB'),
          (1024, 'kB'),
          (1, 'B')]


def _bytes_to_friendly_string(b):
    '''
    Formats the specified integer count of bytes as a friendly string
    with units, e.g. 1024 -> "1kB"
    '''

    # Find the largest unit that evenly divides the input
    unit = next(u for u in _units if (b % u[0]) == 0)

    # Format the value with the chosen unit
    return str((b // unit[0])) + unit[1]

class LongRunningOperationResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    '''
    Long-running operation poller that also transforms the json response.
    '''
    def __init__(self, cli_ctx, transform_func):
        super(LongRunningOperationResultTransform, self).__init__(cli_ctx)
        self._transform_func = transform_func

    def __call__(self, result):
        '''
        Function call operator which will do polling (if necessary)
        and then transforms the result.
        '''

        if result is None:
            return None

        from azure.cli.core.util import poller_classes
        if isinstance(result, poller_classes()):
            # Poll for long-running operation result result by calling base class
            result = super(LongRunningOperationResultTransform, self).__call__(result)

        # Apply transform function
        return self._transform_func(result)


def _apply_format(result, format_group):
    '''
    Applies the specified format_group function to the single result or list of results.
    '''

    # Optionally grab internal 'value' array
    if 'value' in result and isinstance(result['value'], list):
        result = result['value']

    # Get list of results, or make singleton list from single list
    obj_list = result if isinstance(result, list) else [result]

    # Apply format function to list
    return [format_group(item) for item in obj_list]


def transform_sqlvm_group_output(result):
    '''
    Transforms the result of SQL virtual machine group to eliminate unnecessary parameters.
    '''
    from collections import OrderedDict
    from msrestazure.tools import parse_resource_id
    try:
        resource_group = getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']
        wsfc_object = format_wsfc_domain_profile(result.wsfc_domain_profile)
        #Create a dictionary with the relevant parameters
        output = OrderedDict   ([('id', result.id),
                                 ('location', result.location),
                                 ('name', result.name),
                                 ('provisioningState', result.provisioning_state),
                                 ('sqlImageOffer', result.sql_image_offer),
                                 ('sqlImageSku', result.sql_image_sku),
                                 ('resourceGroup', resource_group),
                                 ('wsfcDomainProfile', wsfc_object),
                                 ('tags', result.tags)])
        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        # Return the response object if the formating fails
        return None if isinstance(result, ClientRawResponse) else result


def format_wsfc_domain_profile(result):
    '''
    Formats the WSFCDomainProfile object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.cluster_bootstrap_account is not None:
        order_dict['clusterBootstrapAccount'] = result.cluster_bootstrap_account
    if result.domain_fqdn is not None:
        order_dict['domainFqdn'] = result.domain_fqdn
    if result.ou_path is not None:
        order_dict['ouPath'] = result.ou_path
    if result.cluster_operator_account is not None:
        order_dict['clusterOperatorAccount'] = result.cluster_operator_account
    if result.file_share_witness_path is not None:
        order_dict['fileShareWitnessPath'] = result.file_share_witness_path
    if result.sql_service_account is not None:
        order_dict['sqlServiceAccount'] = result.sql_service_account
    if result.storage_account_url is not None:
        order_dict['storageAccountUrl'] = result.storage_account_url

    return order_dict


def transform_sqlvm_group_list(group_list):
    '''
    Formats the list of results from a SQL virtual machine group
    '''
    return [transform_sqlvm_group_output(v) for v in group_list]
