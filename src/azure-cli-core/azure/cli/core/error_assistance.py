# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser
import json
import openai
import os
import shutil


from azure.cli.core._config import GLOBAL_CONFIG_PATH
from azure.cli.core.style import Style, print_styled_text


def error_assistance(command=None):
    openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')  # Edit to genearalize and keep endpoint secure
    openai.api_version = "2023-07-01-preview"
    openai.api_type = "azure"
    openai.api_base = os.getenv('ENDPOINT')

    if openai.api_key is None or openai.api_key == '':
        print("Azure OpenAI API Key for error assistance is not set.")
        return None

    if command is None:
        return None

    prompt = "Azure CLI Command: '" + command + "'\n This isn't working, why not?"
    messages = [
        {"role": "system", "content": "You receive an Azure CLI command that contains \
         a syntax or command structure error. Find out what the error is and correct it, \
         giving back a corrected command Azure CLI command to the user. \n \
         Example with all the parameters missing: \n \
         Azure CLI Command: storage account create \n \
         Response:The resource group, name, and any other necessary parameters are missing. \n \
         storage account create --resource-group <myResourceGroup> --name <Name>"},
        {"role": "user", "content": prompt}
    ]

    functions = [
        {
            "name": "error_response",
            "description": "Receives an Azure CLI command that triggered an error \
                and checks for any syntactical errors. Provides an explanation as to \
                    what the problem is as well as the corrected command with no additional text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation": {
                        "type": "string",
                        "description": "The explanation of what the user did wrong in their initial command syntax \
                            (i.e. The --name flag is missing before the resource name.)"
                    },
                    "corrected_command": {
                        "type": "string",
                        "description": "The corrected command (i.e. az keyvault create \
                            --name <UniqueKeyvaultName> --resource-group <myResourceGroup> --location <eastus>)"
                    }
                },
                "required": ["explanation", "corrected_command"],
            },
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            deployment_id=os.getenv('DEPLOYMENT'),
            messages=messages,
            functions=functions,
            function_call={"name": "error_response"},
            temperature=0
        )

    except openai.error.OpenAIError as exception:
        print("An error occurred calling Azure OpenAI: ", exception)
        return None

    return response


def print_error_assistance(response):
    args = response['choices'][0]['message']['function_call']['arguments']

    arg_json = json.loads(args)

    explanation = arg_json['explanation']
    corrected_command = validate_command(arg_json['corrected_command'])

    print("\n")
    print_line()
    print_styled_text([(Style.ERROR, "Issue: ")])
    print(explanation)
    print("\n")
    print_styled_text([(Style.ERROR, "Corrected Command: ")])
    print(corrected_command)
    print_line()
    print("\n")


def validate_command(command_response):
    # Incorporate syntax validation here
    # if command syntax is correct:
    return command_response
    # else:
    # return "No command available."


def print_line():
    console_width = shutil.get_terminal_size().columns
    dashed_line = "-" * console_width

    print_styled_text([(Style.ERROR, dashed_line)])


def error_enabled():
    return get_config()


def get_config():
    config = configparser.ConfigParser()

    try:
        config.read(GLOBAL_CONFIG_PATH, encoding='utf-8')

    except configparser.Error as exception:
        print(f"Error reading config file: {exception}")
        return False

    return str_to_bool(config.get('core', 'error_assistance', fallback=False)) \
        or str_to_bool(config.get('interactive', 'error_assistance', fallback=False))


def str_to_bool(string):
    if string == 'True' or string == 'true':
        return True
    return False
