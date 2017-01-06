# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from collections import OrderedDict
import json
import os
import re
import sys

import argparse

from _common import snake_to_camel

# HELPER FUNCTIONS

def get_required(value):
    default_value = value.get('defaultValue')
    if not default_value and default_value != '' \
        and not isinstance(default_value, list) and not isinstance(default_value, dict):
        return swagger_template_required
    return ''

def get_enum(value, name):
    if value.get('allowedValues'):
        enum_text = ',\n'.join(['"{0}"'.format(v) for v in value['allowedValues']])
        return swagger_template_enum.format(enum_text, name)
    return ''

def get_default(value):
    default_value = value.get('defaultValue')
    swagger = ''
    if default_value and (isinstance(default_value, int) or '[' not in default_value) \
        and not isinstance(default_value, list) and not isinstance(default_value, dict):
        swagger = swagger_template_default.format(default_value)
    elif (isinstance(default_value, bool)):
        swagger = swagger_template_default.format(default_value)
    return swagger

def get_type_string(value):
    type = value.get('type')
    type_conversion = {
        'bool': 'boolean',
        'int': 'integer',
        'securestring': 'string'
    }
    type = type_conversion.get(type, type)

    type_string = '"type": "{}"'.format(type)
    if type == 'array':
        type_string = '''
            "type": "{0}",
            "items": {{
              "type": "{1}"
            }}
        '''.format(type, 'object') # Currently only support arrays of objects

    return type_string


def get_required_list(items):
    list = ',\n        '.join(['"{0}"'.format(name) for name, value in items if get_required(value)])
    return swagger_template_required_list.format(list)

# SWAGGER TEMPLATE SNIPPETS

swagger_template_master = '''{{
  "swagger": "2.0",
  "info": {{
    "title": "{3}CreationClient",
    "version": "2015-11-01"
  }},
  "host": "management.azure.com",
  "schemes": [
    "https"
  ],
  "consumes": [
    "application/json"
  ],
  "produces": [
    "application/json"
  ],
  "security": [
    {{
      "azure_auth": [
        "user_impersonation"
      ]
    }}
  ],
  "securityDefinitions": {{
    "azure_auth": {{
      "type": "oauth2",
      "authorizationUrl": "https://login.microsoftonline.com/common/oauth2/authorize",
      "flow": "implicit",
      "description": "Azure Active Directory OAuth2 Flow",
      "scopes": {{
        "user_impersonation": "impersonate your user account"
      }}
    }}
  }},
  "paths": {{
    "/subscriptions/{{subscriptionId}}/resourcegroups/{{resourceGroupName}}/providers/Microsoft.Resources/deployments/{{deploymentName}}": {{
      "put": {{
        "tags": [
          "{3}"
        ],
        "operationId": "{3}_CreateOrUpdate",
        "description": "Create a new {3}.",
        "parameters": [
          {{
            "name": "resourceGroupName",
            "in": "path",
            "required": true,
            "type": "string",
            "description": "The name of the resource group. The name is case insensitive.",
            "pattern": "^[-\\\\w\\\\._]+$",
            "minLength": 1,
            "maxLength": 64
          }},
          {{
            "name": "deploymentName",
            "in": "path",
            "required": true,
            "type": "string",
            "description": "The name of the deployment.",
            "pattern": "^[-\\\\w\\\\._]+$",
            "minLength": 1,
            "maxLength": 64
          }},
          {{
            "name": "parameters",
            "x-ms-client-flatten": true,
            "in": "body",
            "required": true,
            "schema": {{
              "$ref": "#/definitions/Deployment_{3}"
            }},
            "description": "Additional parameters supplied to the operation."
          }},
          {{
            "$ref": "#/parameters/ApiVersionParameter"
          }},
          {{
            "$ref": "#/parameters/SubscriptionIdParameter"
          }}
        ],
        "responses": {{
          "200": {{
            "description": "",
            "schema": {{
              "$ref": "#/definitions/DeploymentExtended"
            }}
          }},
          "201": {{
            "description": "",
            "schema": {{
              "$ref": "#/definitions/DeploymentExtended"
            }}
          }}
        }},
        "x-ms-long-running-operation": true
      }}
    }}
  }},
  "definitions": {{
    "Deployment_{3}": {{
      "properties": {{
        "properties": {{
          "$ref": "#/definitions/DeploymentProperties_{3}",
          "description": "Gets or sets the deployment properties.",
          "x-ms-client-flatten": true
        }}
      }},
      "description": "Deployment operation parameters."
    }},
    "DeploymentProperties_{3}": {{
      "properties": {{
        "templateLink": {{
          "$ref": "#/definitions/TemplateLink",
          "description": "Gets or sets the URI referencing the template. Use only one of Template or TemplateLink.",
          "x-ms-client-flatten": true
        }},
        "parameters": {{
          "$ref": "#/definitions/{3}Parameters",
          "type": "object",
          "description": "Deployment parameters. Use only one of Parameters or ParametersLink.",
          "x-ms-client-flatten": true
        }},
        "mode": {{
          "type": "string",
          "description": "Gets or sets the deployment mode.",
          "enum": [
            "Incremental"
          ],
          "x-ms-enum": {{
            "name": "DeploymentMode",
            "modelAsString": false
          }}
        }}
      }},
      "required": [
        "templateLink",
        "parameters",
        "mode"
      ],
      "description": "Deployment properties."
    }},
    "TemplateLink": {{
      "properties": {{
        "uri": {{
          "type": "string",
          "description": "URI referencing the template.",
          "enum": [
            "https://azuresdkci.blob.core.windows.net/templatehost/Create{3}_{4}/azuredeploy.json"
          ]
        }},
        "contentVersion": {{
          "type": "string",
          "description": "If included it must match the ContentVersion in the template."
        }}
      }},
      "required": [
        "uri"
      ],
      "description": "Entity representing the reference to the template."
    }},
    "{3}Parameters": {{
      {0}{1}
    }},
    {2},
    "ParametersLink": {{
      "properties": {{
        "uri": {{
          "type": "string",
          "description": "URI referencing the template."
        }},
        "contentVersion": {{
          "type": "string",
          "description": "If included it must match the ContentVersion in the template."
        }}
      }},
      "required": [
        "uri"
      ],
      "description": "Entity representing the reference to the deployment parameters."
    }},
    "ProviderResourceType": {{
      "properties": {{
        "resourceType": {{
          "type": "string",
          "description": "Gets or sets the resource type."
        }},
        "locations": {{
          "type": "array",
          "items": {{
            "type": "string"
          }},
          "description": "Gets or sets the collection of locations where this resource type can be created in."
        }},
        "apiVersions": {{
          "type": "array",
          "items": {{
            "type": "string"
          }},
          "description": "Gets or sets the api version."
        }},
        "properties": {{
          "type": "object",
          "additionalProperties": {{
            "type": "string"
          }},
          "description": "Gets or sets the properties."
        }}
      }},
      "description": "Resource type managed by the resource provider."
    }},
    "Provider": {{
      "properties": {{
        "id": {{
          "type": "string",
          "description": "Gets or sets the provider id."
        }},
        "namespace": {{
          "type": "string",
          "description": "Gets or sets the namespace of the provider."
        }},
        "registrationState": {{
          "type": "string",
          "description": "Gets or sets the registration state of the provider."
        }},
        "resourceTypes": {{
          "type": "array",
          "items": {{
            "$ref": "#/definitions/ProviderResourceType"
          }},
          "description": "Gets or sets the collection of provider resource types."
        }}
      }},
      "description": "Resource provider information."
    }},
    "BasicDependency": {{
      "properties": {{
        "id": {{
          "type": "string",
          "description": "Gets or sets the ID of the dependency."
        }},
        "resourceType": {{
          "type": "string",
          "description": "Gets or sets the dependency resource type."
        }},
        "resourceName": {{
          "type": "string",
          "description": "Gets or sets the dependency resource name."
        }}
      }},
      "description": "Deployment dependency information."
    }},
    "Dependency": {{
      "properties": {{
        "dependsOn": {{
          "type": "array",
          "items": {{
            "$ref": "#/definitions/BasicDependency"
          }},
          "description": "Gets the list of dependencies."
        }},
        "id": {{
          "type": "string",
          "description": "Gets or sets the ID of the dependency."
        }},
        "resourceType": {{
          "type": "string",
          "description": "Gets or sets the dependency resource type."
        }},
        "resourceName": {{
          "type": "string",
          "description": "Gets or sets the dependency resource name."
        }}
      }},
      "description": "Deployment dependency information."
    }},
    "DeploymentPropertiesExtended": {{
      "properties": {{
        "provisioningState": {{
          "type": "string",
          "description": "Gets or sets the state of the provisioning."
        }},
        "correlationId": {{
          "type": "string",
          "description": "Gets or sets the correlation ID of the deployment."
        }},
        "timestamp": {{
          "type": "string",
          "format": "date-time",
          "description": "Gets or sets the timestamp of the template deployment."
        }},
        "outputs": {{
          "type": "object",
          "description": "Gets or sets key/value pairs that represent deploymentoutput."
        }},
        "providers": {{
          "type": "array",
          "items": {{
            "$ref": "#/definitions/Provider"
          }},
          "description": "Gets the list of resource providers needed for the deployment."
        }},
        "dependencies": {{
          "type": "array",
          "items": {{
            "$ref": "#/definitions/Dependency"
          }},
          "description": "Gets the list of deployment dependencies."
        }},
        "template": {{
          "type": "object",
          "description": "Gets or sets the template content. Use only one of Template or TemplateLink."
        }},
        "TemplateLink": {{
          "$ref": "#/definitions/TemplateLink",
          "description": "Gets or sets the URI referencing the template. Use only one of Template or TemplateLink."
        }},
        "parameters": {{
          "type": "object",
          "description": "Deployment parameters. Use only one of Parameters or ParametersLink."
        }},
        "parametersLink": {{
          "$ref": "#/definitions/ParametersLink",
          "description": "Gets or sets the URI referencing the parameters. Use only one of Parameters or ParametersLink."
        }},
        "mode": {{
          "type": "string",
          "description": "Gets or sets the deployment mode.",
          "enum": [
            "Incremental",
            "Complete"
          ],
          "x-ms-enum": {{
            "name": "DeploymentMode",
            "modelAsString": false
          }}
        }}
      }},
      "description": "Deployment properties with additional details."
    }},
    "DeploymentExtended": {{
      "properties": {{
        "id": {{
          "type": "string",
          "description": "Gets or sets the ID of the deployment."
        }},
        "name": {{
          "type": "string",
          "description": "Gets or sets the name of the deployment."
        }},
        "properties": {{
          "$ref": "#/definitions/DeploymentPropertiesExtended",
          "description": "Gets or sets deployment properties."
        }}
      }},
      "required": [
        "name"
      ],
      "description": "Deployment information."
    }}
  }},
  "parameters": {{
    "SubscriptionIdParameter": {{
      "name": "subscriptionId",
      "in": "path",
      "required": true,
      "type": "string",
      "description": "Gets subscription credentials which uniquely identify Microsoft Azure subscription. The subscription ID forms part of the URI for every service call."
    }},
    "ApiVersionParameter": {{
      "name": "api-version",
      "in": "query",
      "required": true,
      "type": "string",
      "description": "Client Api Version."
    }}
  }}
}}
'''

swagger_props_template = '''
"properties": {{
{0}
}}
'''

swagger_template_prop = '''  "{0}": {{
    "type": "object",
    "$ref": "#/definitions/DeploymentParameter_{0}",
    "x-ms-client-flatten": true
  }}'''

swagger_template_param = '''"DeploymentParameter_{0}": {{
  "properties": {{
    "value": {{
      {5},
      "description": "{1}",
      "x-ms-client-name": "{0}"{3}{4}
    }}
  }}{2}
}}'''

swagger_template_artifacts_location = '''
"DeploymentParameter__artifactsLocation": {{
      "properties": {{
        "value": {{
          "type": "string",
          "description": "Container URI of of the template.",
          "x-ms-client-name": "_artifactsLocation",
          "enum": [
            "https://azuresdkci.blob.core.windows.net/templatehost/Create{0}_{1}"
          ]
        }}
      }},
      "required": [
        "value"
      ]
    }}'''

swagger_template_required = ''',
      "required": [
        "value"
      ]
'''

swagger_template_enum = ''',
      "enum": [
        {0}
      ],
      "x-ms-enum": {{
        "name": "{1}",
        "modelAsString": false
      }}'''

swagger_template_default = ''',
      "default": "{0}"'''

swagger_template_required_list = ''',
      "required": [
        {0}
      ]
'''

def convert_template_to_swagger(*args):

    # Create script parser

    print('\n== CONVERT TEMPLATE TO SWAGGER ==')

    parser = argparse.ArgumentParser(description='ARM Template to Swagger')
    parser.add_argument('--name', metavar='NAME', required=True, help='Name of the thing being created (in snake_case)')
    parser.add_argument('--src', metavar='PATH', required=True, help='Path to the ARM template file to convert.')
    parser.add_argument('--api-version', metavar='VERSION', required=True, help='API version for the template being generated in yyyy-MM-dd format. (ex: 2016-07-01)')
    args = parser.parse_args(args)

    api_version = args.api_version
    src = args.src
    name = args.name

    if not os.path.isfile(src):
        raise RuntimeError('File {} not found.'.format(src))

    root, src_file = os.path.split(src)
    dest = os.path.join(root, 'swagger_create_{}.json'.format(name))

    # Convert template to swagger
    with open(src) as f:
        j = json.load(f)
    
        print('Converting ARM template {} to swagger.'.format(src_file))
        params = j['parameters']
        prop_strings = [swagger_template_prop.format(key) 
            for key, value in sorted(params.items(), key=lambda item: item[0])]
        props_section = swagger_props_template.format(',\n        '.join(prop_strings))

        param_strs = []
        for key, value in sorted(params.items(), key=lambda item: item[0]):
            comment = value['metadata'].get('description') if value['metadata'] else None
            if not comment:
                print('FAILURE: Description metadata is required for all parameters. Not found for {}'.format(value))
                sys.exit(-1)
            param_strs.append(swagger_template_param.format(
                key, comment or '', get_required(value), get_enum(value, key), get_default(value), get_type_string(value)))

        # artifacts special case
        artifacts_paramstr = next((p for p in param_strs if '_artifacts' in p), None)
        if artifacts_paramstr:
            param_strs.remove(artifacts_paramstr)
            param_strs.append(swagger_template_artifacts_location.format(snake_to_camel(name), api_version))

        params_section = ',\n'.join(param_strs)

        with open(dest, 'w') as output_file:
            raw_swagger = swagger_template_master.format(props_section, get_required_list(params.items()), params_section, snake_to_camel(name), api_version)
            output_file.write(json.dumps(json.loads(raw_swagger, object_pairs_hook=OrderedDict), indent=2))
            print('{} generated successfully.'.format(dest))

    return dest

if __name__ == '__main__':
    convert_template_to_swagger(*sys.argv[1:])
