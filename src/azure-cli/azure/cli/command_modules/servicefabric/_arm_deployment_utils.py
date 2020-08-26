# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.profiles import ResourceType
from knack.log import get_logger
from ._client_factory import (resource_client_factory)

logger = get_logger(__name__)


def validate_and_deploy_arm_template(cmd, resource_group_name, template, parameters):
    suffix = datetime.datetime.now().strftime("%Y%m%d%H%M")
    deployment_name = 'AzurePSDeployment-' + suffix

    logger.info("Validating the deployment")
    validate_result = _deploy_arm_template_core(
        cmd, resource_group_name, template, parameters, deployment_name, 'incremental', True)
    if validate_result.error is not None:
        errors_detailed = _build_detailed_error(validate_result.error, [])
        errors_detailed.insert(0, "Error validating template. See below for more information.")
        raise CLIError('\n'.join(errors_detailed))
    logger.info("Deployment is valid, and begin to deploy")
    _deploy_arm_template_core(cmd, resource_group_name, template,
                              parameters, deployment_name, 'incremental', False)


def _deploy_arm_template_core(cmd,
                              resource_group_name,
                              template,
                              parameters,
                              deployment_name=None,
                              mode='incremental',
                              validate_only=False,
                              no_wait=False):
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    properties = DeploymentProperties(
        template=template, template_link=None, parameters=parameters, mode=mode)
    client = resource_client_factory(cmd.cli_ctx)

    if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
        Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
        deployment = Deployment(properties=properties)

        if validate_only:
            deploy_poll = sdk_no_wait(no_wait, client.deployments.validate, resource_group_name, deployment_name,
                                      deployment)
        else:
            deploy_poll = sdk_no_wait(no_wait, client.deployments.create_or_update, resource_group_name,
                                      deployment_name, deployment)
        return LongRunningOperation(cmd.cli_ctx)(deploy_poll)

    if validate_only:
        deploy_poll = sdk_no_wait(no_wait, client.deployments.validate, resource_group_name, deployment_name,
                                  properties)
    else:
        deploy_poll = sdk_no_wait(no_wait, client.deployments.create_or_update, resource_group_name, deployment_name,
                                  properties)
    return LongRunningOperation(cmd.cli_ctx)(deploy_poll)


def _build_detailed_error(top_error, output_list):
    if output_list:
        output_list.append(' Inner Error - Code: "{}" Message: "{}"'.format(top_error.code, top_error.message))
    else:
        output_list.append('Error - Code: "{}" Message: "{}"'.format(top_error.code, top_error.message))

    if top_error.details:
        for error in top_error.details:
            _build_detailed_error(error, output_list)

    return output_list
