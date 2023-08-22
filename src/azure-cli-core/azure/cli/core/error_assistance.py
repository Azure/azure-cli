import openai
import json
import shutil
import configparser

from azure.cli.core._config import GLOBAL_CONFIG_PATH

def error_assistance(command, message=None):      
        openai.api_key = <api-key>
        openai.api_version = "2023-07-01-preview"
        openai.api_type = "azure"
        openai.api_base = <endpoint>

        if message==None:
                prompt = "Azure CLI Command: " + command + ", This isn't working, why not?"
        #elif command is not None:
         #       prompt = "Azure CLI Command: " + command + ", Azure CLI Error: " + message + ", What did I do wrong?"
        else:
                prompt = "Azure CLI Error: " + message + ", What did I do wrong?"

        messages = [
                {"role": "system", "content": "You are a helpful assistant that provides concise explanations about the Azure CLI error provided and provides a remedied command."},
                {"role": "user", "content": prompt}
        ]

        functions = [  
            {
                "name": "error_response",
                "description": "Receives an Azure CLI error message and the user's command (with parameter values removed) that triggered the error and provides an explanation as to what the problem is as well as the corrected command without any additional text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "explanation": {
                            "type": "string",
                            "description": "The explanation of what the user did wrong in their initial command (i.e. The --name flag is missing before the resource name.)"
                        },
                        "corrected_command": {
                            "type": "string",
                            "description": "The corrected command (i.e. az keyvault create --name <UniqueKeyvaultName> --resource-group <myResourceGroup> --location <eastus>)"
                        }
                    },
                    "required": ["explanation", "corrected_command"],
                },
            }
        ]   

        response = openai.ChatCompletion.create(
            deployment_id="openai-interns-model",
            messages=messages,
            functions=functions,
            function_call={"name": "error_response"}, 
        )

        return response

def print_error_assistance(response):
        args = response['choices'][0]['message']['function_call']['arguments']

        arg_json = json.loads(args)

        explanation = arg_json['explanation']
        corrected_command = validate_command(arg_json['corrected_command'])
        
        print("\n")
        print_line()
        print("\x1b[91mIssue: \x1b[0m")
        print(explanation)
        print("\n")
        print("\x1b[91mCorrected Command: \x1b[0m")
        print(corrected_command)
        print_line()
        print("\n")

def validate_command(command_response):
        #if command syntax is correct:
                return command_response
        #else:
                return "No command available."


def print_line():
        console_width = shutil.get_terminal_size().columns
        dashed_line = "\x1b[91m-\x1b[0m" * console_width

        print(dashed_line)
        
def error_enabled():
        enabled = get_config()
        if enabled:
                return True
        return False

def get_config():
        config = configparser.ConfigParser()
        config.read(GLOBAL_CONFIG_PATH)
        return str_to_bool(config.get('core', 'error_assistance', fallback=False)) or str_to_bool(config.get('interactive', 'error_assistance', fallback=False))

def str_to_bool(string):
        if string=='True' or string=='true':
                return True
        else:
                return False
