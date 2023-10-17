# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=bare-except
from azure.cli.command_modules.containerapp._utils import safe_get


def transform_containerapp_output(app):
    props = ['name', 'location', 'resourceGroup', 'provisioningState']
    result = {k: app[k] for k in app if k in props}

    try:
        result['fqdn'] = app['properties']['configuration']['ingress']['fqdn']
    except:
        result['fqdn'] = None

    return result


def clean_up_sensitive_values(response_json):
    for container in safe_get(response_json, "properties", "template", "containers", default=[]):
        if "env" in container:
            for env in container["env"]:
                if env.get("value"):
                    del env["value"]

    if safe_get(response_json, "properties", "template") and "scale" in response_json["properties"]["template"]:
        for rule in safe_get(response_json, "properties", "template", "scale", "rules", default=[]):
            for (key, val) in rule.items():
                if key != "name":
                    val["metadata"] = dict((k, "") for k, v in val["metadata"].items())
    return response_json


def transform_sensitive_values_wrapper():

    def transform_sensitive_values(response_json):
        return clean_up_sensitive_values(response_json)

    return transform_sensitive_values


def transform_sensitive_values_list_output_wrapper():

    def transform_sensitive_values_list_output(apps):
        return [clean_up_sensitive_values(a) for a in apps]

    return transform_sensitive_values_list_output


def transform_containerapp_list_output(apps):
    return [transform_containerapp_output(a) for a in apps]


def transform_revision_output(rev):
    props = ['name', 'active', 'createdTime', 'trafficWeight', 'healthState', 'provisioningState', 'replicas']
    result = {k: rev['properties'][k] for k in rev['properties'] if k in props}

    if 'name' in rev:
        result['name'] = rev['name']

    if 'fqdn' in rev['properties']['template']:
        result['fqdn'] = rev['properties']['template']['fqdn']

    return result


def transform_revision_list_output(revs):
    return [transform_revision_output(r) for r in revs]


def transform_job_execution_show_output(execution):
    return {
        'name': execution['name'],
        'startTime': execution['properties']['startTime'],
        'status': execution['properties']['status']
    }


def transform_job_execution_list_output(executions):
    return [transform_job_execution_show_output(e) for e in executions]
