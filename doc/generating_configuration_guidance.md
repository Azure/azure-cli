# Generating Configuration Guidance

[Azdev](https://github.com/Azure/azure-cli-dev-tools) supports to generate a snapshot of command interfaces for a specified module since version 0.2.0.

## Output

### Folder structure
After generation, there will be a folder named `configuration` under the module dir. The subdirectories of `configuration` are named by profiles, such as `latest`, `2020-09-01-hybrid` and `2019-03-01-hybrid`.
Each profile named folder contains two json files named `commands.json` and `examples.json` respectively.

```
- <module dir>
    - ...
    - configuration
        - latest
            - commands.json
            - examples.json
        - 2020-09-01-hybrid
            - commands.json
            - examples.json
        - <other profile name>
            - commands.json
            - examples.json
```

### Simple Schema of `commands.json`

```json
{
  "az": {
    "command-groups": {
      "network": {
        "full-name": "network",
        "help": "Manage Azure Network resources.",
        "commands": {
          "list-service-aliases": {
            "full-name": "network list-service-aliases",
            ...
          },
          "list-service-tags": {
            "full-name": "network list-service-tags",
            ...
          }
        },
        "command-groups": {
          "application-gateway": {
            "full-name": "network application-gateway",
            "help": {
              "short-summary": "Manage application-level routing and load balancing services.",
              "long-summary": "To learn more about Application Gateway, visit https://docs.microsoft.com/azure/application-gateway/application-gateway-create-gateway-cli"
            },
            "commands": {
              "create": {
                "full-name": "network application-gateway create",
                "help": "Create an application gateway.",
                "operation": "@.custom#create_application_gateway",
                "arguments": {
                  "application_gateway_name": {
                    ...
                  },
                  "connection_draining_timeout": {
                    "min-api": "2016-12-01",
                    "options": [
                      "--connection-draining-timeout"
                    ],
                    "help": "The time in seconds after a backend server is removed during which on open connection remains active. Range: 0 (disabled) to 3600",
                    "arg-group": "Gateway"
                  }
                }
              },
              "delete": {
                "full-name": "network application-gateway delete",
                ...
              }
            },
            "command-groups": {
              "address-pool": {
                "full-name": "network application-gateway address-pool",
                ...
              },
              "auth-cert": {
                "full-name": "network application-gateway auth-cert",
                ...
              }
            }
          },
          "dns": {
            "full-name": "network dns",
            ...
          },
          "lb": {
            "full-name": "network lb",
            ...
          }
        }
      }
    }
  }
}
```

### Simple Schema of `examples.json`

```json


```

