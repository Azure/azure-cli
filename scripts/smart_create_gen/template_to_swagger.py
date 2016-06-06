from __future__ import print_function

import json
import os
import re
import sys

import argparse

from _common import to_snake_case, get_name_from_path, validate_src, parser

# HELPER FUNCTIONS

def get_required(value):
    if not value.get('defaultValue') and value.get('defaultValue') != '':
        return swagger_template_required
    return ''

def get_enum(value):
    if value.get('allowedValues'):
        return swagger_template_enum.format(',\n        '.join(['"{0}"'.format(v) for v in value['allowedValues']]))
    return ''

def get_default(value):
    if value.get('defaultValue') and (isinstance(value.get('defaultValue'), int) or '[' not in value.get('defaultValue')):
        return swagger_template_default.format(value.get('defaultValue', ''))
    return ''

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
        "description": "Create or update a virtual machine.",
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
      "description": "Entity representing the reference to the deployment paramaters."
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
      "type": "string",
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
      ]'''

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

    args = parser.parse_args(args)

    api_version = args.api_version
    root = args.src or os.getcwd()
    name = get_name_from_path(root)
    src = os.path.join(root, 'azuredeploy.json')
    validate_src(src)
    dest = os.path.join(root, 'swagger_create_{}.json'.format(to_snake_case(name)))

    # Convert template to swagger
    with open(src) as f:
        j = json.load(f)
    
        print('Converting ARM template {} to swagger.'.format(src))
        prms = j['parameters']
        propstrs = [swagger_template_prop.format(name)
                    for name, value in sorted(prms.items(), key=lambda item: item[0])]
        tml = swagger_props_template.format(',\n        '.join(propstrs))

        prmstrs = [swagger_template_param.format(name,
                                                 value['metadata']['description'],
                                                 get_required(value),
                                                 get_enum(value),
                                                 get_default(value))
                   for name, value in sorted(prms.items(), key=lambda item: item[0])]

        # artifacts special case
        artifacts_prmstr = next((p for p in prmstrs if '_artifacts' in p), None)
        if artifacts_prmstr:
            prmstrs.remove(artifacts_prmstr)
            prmstrs.append(swagger_template_artifacts_location.format(name, api_version))

        tml2 = ',\n'.join(prmstrs)

        with open(dest, 'w') as output_file:
            raw_swagger = swagger_template_master.format(tml, get_required_list(prms.items()), tml2, name, api_version)
            output_file.write(json.dumps(json.loads(raw_swagger), indent=2))
            print('{} generated successfully.'.format(dest))

    return dest

if __name__ == '__main__':
    convert_template_to_swagger(*sys.argv[1:])