import json
import os
import openai
import requests

def error_assistance(prompt, error_message):      
        headers = {
        'Content-Type': 'application/json',
        'api-key': <api-key>
        }

        revised_prompt = "Azure CLI Command: " + prompt + ", Error received: " + error_message + ". What am I doing wrong?"

        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that provides concise explanations about the Azure CLI error provided and provides a remedied command."},
                {"role": "user", "content": revised_prompt}
            ]
        }

        url = 'https://internsopenai.openai.azure.com/openai/deployments/openai-interns-model/chat/completions?api-version=2023-05-15'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"API call failed with status code {response.status_code}: {response.text}")
            return None

        return response
