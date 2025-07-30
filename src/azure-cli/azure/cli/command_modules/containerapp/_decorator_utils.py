# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, no-else-return, duplicate-string-formatting-argument, expression-not-assigned, too-many-locals, logging-fstring-interpolation, broad-except, pointless-statement, bare-except
import sys

from azure.cli.core.azclierror import (ValidationError)

from ._utils import safe_get


def load_yaml_file(file_name):
    import yaml
    import errno

    try:
        with open(file_name) as stream:  # pylint: disable=unspecified-encoding
            return yaml.safe_load(stream.read().replace('\x00', ''))
    except OSError as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise ValidationError('{} does not exist'.format(file_name)) from ex
        raise
    except (yaml.parser.ParserError, UnicodeDecodeError) as ex:
        raise ValidationError('Error parsing {} ({})'.format(file_name, str(ex))) from ex


def create_deserializer(models):
    from msrest import Deserializer
    import inspect
    from importlib import import_module

    import_module(models)

    sdkClasses = inspect.getmembers(sys.modules[models])
    deserializer = {}

    for sdkClass in sdkClasses:
        deserializer[sdkClass[0]] = sdkClass[1]

    return Deserializer(deserializer)


def process_loaded_yaml(yaml_containerapp):
    if not isinstance(yaml_containerapp, dict):  # pylint: disable=unidiomatic-typecheck
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.')
    if not yaml_containerapp.get('properties'):
        yaml_containerapp['properties'] = {}

    if safe_get(yaml_containerapp, "identity", "userAssignedIdentities"):
        for identity in yaml_containerapp['identity']['userAssignedIdentities']:
            # properties (principalId and clientId) are readonly and create (PUT) will throw error if they are provided
            # Update (PATCH) ignores them, so it's okay to remove them as well
            yaml_containerapp['identity']['userAssignedIdentities'][identity] = {}

    nested_properties = ["provisioningState",
                         "managedEnvironmentId",
                         "environmentId",
                         "latestRevisionName",
                         "latestRevisionFqdn",
                         "customDomainVerificationId",
                         "configuration",
                         "template",
                         "outboundIPAddresses",
                         "workloadProfileName",
                         "latestReadyRevisionName",
                         "eventStreamEndpoint",
                         "runningStatus"]
    for nested_property in nested_properties:
        tmp = yaml_containerapp.get(nested_property)
        if nested_property in yaml_containerapp:
            yaml_containerapp['properties'][nested_property] = tmp
            del yaml_containerapp[nested_property]
    # remove property managedEnvironmentId, can not use safe_get()
    if "managedEnvironmentId" in yaml_containerapp['properties']:
        tmp = yaml_containerapp['properties']['managedEnvironmentId']
        if tmp:
            yaml_containerapp['properties']["environmentId"] = tmp
        del yaml_containerapp['properties']['managedEnvironmentId']

    return yaml_containerapp
