import openai
import json
import shutil

from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.containers import VSplit, HSplit, Window, FloatContainer, Float, ConditionalContainer
from prompt_toolkit.layout.controls import FillControl
from pygments.token import Token

def error_assistance(prompt, error_message):      
        openai.api_key = <api-key>
        openai.api_version = "2023-07-01-preview"
        openai.api_type = "azure"
        openai.api_base = <endpoint>

        revised_prompt = "Azure CLI Command: " + prompt + ", Error received: " + error_message + ". What am I doing wrong?"

        messages = [
                {"role": "system", "content": "You are a helpful assistant that provides concise explanations about the Azure CLI error provided and provides a remedied command."},
                {"role": "user", "content": revised_prompt}
        ]

        functions = [  
            {
                "name": "error_response",
                "description": "Receives an Azure CLI error message and the user's command and provides an explanation as to what the problem is as well as the corrected command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "explanation": {
                            "type": "string",
                            "description": "The explanation of what the user did wrong in their initial command"
                        },
                        "corrected_command": {
                            "type": "string",
                            "description": "The corrected command"
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
        corrected_command = arg_json['corrected_command']

        
        print("\n")
        print_line()
        print("Issue: ")
        print(explanation)
        print("\n")
        print("Corrected Command: ")
        print(corrected_command)
        print_line()

def print_line():
        console_width = shutil.get_terminal_size().columns
        dashed_line = "-" * console_width

        print(dashed_line)
        
