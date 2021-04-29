# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
config = {
    "core": {
        "output": {
            "default": "json",
            "allowed": [
                {
                    "value": "json",
                    "description": "JSON formatted output that most closely matches API responses."
                },
                {
                    "value": "jsonc",
                    "description": "Colored JSON formatted output that most closely matches API responses."
                },
                {
                    "value": "table",
                    "description": "Human-readable output format."
                },
                {
                    "value": "tsv",
                    "description": "Tab- and Newline-delimited. Great for GREP, AWK, etc."
                },
                {
                    "value": "yaml",
                    "description": "YAML formatted output. An alternative to JSON. Great for configuration files."
                },
                {
                    "value": "yamlc",
                    "description": "Colored YAML formatted output. An alternative to JSON. Great for configuration files."
                },
                {
                    "value": "none",
                    "description": "No output, except for errors and warnings."
                }
            ],
            "type": "string",
            "description": "The default output format."
        },
        "disable_confirm_prompt": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Commands will not wait for user confirmation."
                },
                {
                    "value": "false",
                    "description": "Commands will wait for user confirmation."
                }
            ],
            "type": "boolean",
            "description": "Turn confirmation prompts on/off"
        }, 
        "collect_telemetry": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Allow anonymous data collection."
                },
                {
                    "value": "false",
                    "description": "Do not allow anonymous data collection."
                }
            ],
            "type": "boolean",
            "description": "Allow Microsoft to collect anonymous data on the usage of the CLI."
        },
        "only_show_errors": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Only print errors to sterr. Supress warnings from preview, deprecated and experiental commands"
                },
                {
                    "value": "false",
                    "description": "Do not supress output."
                }
            ],
            "type": "boolean",
            "description": "Only show errors during command invocation. In other words, only errors will be written to stderr. It suppresses warnings from preview, deprecated and experimental commands. It is also available for individual commands with the --only-show-errors parameter."
        },
        "no_color": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Disable color in output."
                },
                {
                    "value": "false",
                    "description": "Allow color in output."
                }
            ],
            "type": "boolean",
            "description": "Disable color. Originally colored messages will be prefixed with DEBUG, INFO, WARNING and ERROR. This bypasses the issue of a third-party library where the terminal's color cannot revert back after a stdout redirection."
        },
        "theme": {
            "default": "dark",
            "allowed": [
                {
                    "value": "dark",
                    "description": ""
                },
                {
                    "value": "light",
                    "description": ""
                },
                {
                    "value": "none",
                    "description": ""
                }
            ],
            "type": "string",
            "description": "Color theme for terminal."
        },
        "cache_ttl": {
            "default": "10",
            "allowed": [],
            "type": "integer",
            "description": "How long (in minutes) to before invalidating cache"
        }
    },
    "cloud": {
        "name": {
            "default": "AzureCloud",
            "allowed": [
                {
                    "value": "AzureCloud",
                    "description": ""
                },
                {
                    "value": "AzureChinaCloud",
                    "description": ""
                },
                {
                    "value": "AzureUSGovernment",
                    "description": ""
                },
                {
                    "value": "AzureGermanCloud",
                    "description": ""
                },
                {
                    "value": "Other registered cloud - More information about registering new cloud: https://docs.microsoft.com/en-us/cli/azure/manage-clouds-azure-cli#register-a-new-cloud",
                    "description": ""
                }
            ],
            "type": "string",
            "description": "The default cloud for all az commands"
        }
    },
    "query": {
        "allow_list": {
            "default": "list, show",
            "allowed": [
                {
                    "value": "list",
                    "description": ""
                },
                {
                    "value": "show",
                    "description": ""
                },
                {
                    "value": "version",
                    "description": ""
                },
                {
                    "value": "'' (leave blank)",
                    "description": "Do not generate query examples."
                }
            ],
            "type": "Comma separated values",
            "description": "Generate JMESPath query examples for commands ending with string in this list."
        },
        "examples_len": {
            "default": "80",
            "allowed": [],
            "type": "integer",
            "description": "Maximum length for example query string"
        },
        "help_len": {
            "default": "80",
            "allowed": [],
            "type": "integer",
            "description": "Maximum length for example help string"
        },
        "max_exmples": {
            "default": "80",
            "allowed": [],
            "type": "integer",
            "description": "Maximum number of examples to generate"
        }
    },
    "extension": {
        "use_dynamic_install": {
            "default": "no",
            "allowed": [
                {
                    "value": "no",
                    "description": "When running command that requires extension, do not install extension if not already added."
                },
                {
                    "value": "yes_prompt",
                    "description": "Notify user that extension is required, request permission to add it."
                },
                {
                    "value": "yes_without_prompt",
                    "description": "Do not request user permission to add extension."
                }
            ],
            "type": "string",
            "description": "Default install behavior when extension is required to run command and is not installed."
        },
        "run_after_dynamic_install": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Continue after extension is installed."
                },
                {
                    "value": "false",
                    "description": "Do not continue after extension is instealled."
                }
            ],
            "type": "boolean",
            "description": "Whether or not the command continues when extension is dynamically installed for it."
        }
    },
    "logging": {
        "enable_log_file": {
            "default": "false",
            "allowed": [
                {
                    "value": "true",
                    "description": "Turn logging off"
                },
                {
                    "value": "false",
                    "description": "Turn logging off."
                }
            ],
            "type": "boolean",
            "description": "Turn logging on/off"
        },
        "log_dir": {
            "default": "${AZURE_CONFIG_DIR}/logs*",
            "type": "string",
            "allowed": [
                {
                    "value": "Any path with write access."
                }
            ],
            "description": "Directory to write logs to, only used when enable_log_file is set to true."
        }
    }
}
