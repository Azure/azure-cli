# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-arguments

from collections import OrderedDict
import json

from enum import Enum

from azure.cli.core.util import b64encode


class ArmTemplateBuilder(object):

    def __init__(self):
        template = OrderedDict()
        template['$schema'] = \
            'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
        template['contentVersion'] = '1.0.0.0'
        template['parameters'] = {}
        template['variables'] = {}
        template['resources'] = []
        template['outputs'] = {}
        self.template = template

    def add_resource(self, resource):
        self.template['resources'].append(resource)

    def add_output(self, name, admin_name):
        output = {
            "masterFQDN": {
                "type": "string",
                "value": "[reference(concat('Microsoft.ContainerService/containerServices/', '{}')).masterProfile.fqdn]".format(name)
            },
            "sshMaster0": {
                "type": "string",
                "value": "[concat('ssh ', '{}', '@', reference(concat('Microsoft.ContainerService/containerServices/', '{}')).masterProfile.fqdn, ' -A -p 2200')]".format(admin_name, name)
            },
            "agentFQDN": {
                "type": "string",
                "value": "[reference(concat('Microsoft.ContainerService/containerServices/', '{}')).agentPoolProfiles[0].fqdn]".format(name)
            }
        }
        self.template['outputs'] = output

    def build(self):
        return json.loads(json.dumps(self.template))


def build_acs_resource(name, location, tags, orchestrator_type,
                       master_count, masters_endpoint_dns_name_prefix,
                       agent_count, agent_vm_size, agents_endpoint_dns_name_prefix,
                       admin_username, ssh_key_value):
    acs = {
      "apiVersion": "2016-03-30",
      "type": "Microsoft.ContainerService/containerServices",
      "location": location,
      "tags": tags,
      "name": name,
      "properties": {
        "orchestratorProfile": {
          "orchestratorType": orchestrator_type
        },
        "masterProfile": {
          "count": master_count,
          "dnsPrefix": masters_endpoint_dns_name_prefix
        },
        "agentPoolProfiles": [
          {
            "name": "agentpools",
            "count": agent_count,
            "vmSize": agent_vm_size,
            "dnsPrefix": agents_endpoint_dns_name_prefix
          }
        ],
        "linuxProfile": {
          "adminUsername": admin_username,
          "ssh": {
            "publicKeys": [
              {
                "keyData": ssh_key_value
              }
            ]
          }
        }
      }
    }
    return acs


