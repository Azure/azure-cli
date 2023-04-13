# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.prompting import prompt, prompt_pass


class AAZPromptInput:

    def __init__(self, msg, help_string=None):
        self._msg = msg
        self._help_string = help_string

    def __call__(self, *args, **kwargs):
        return prompt(msg=self._msg, help_string=self._help_string)


class AAZPromptPasswordInput(AAZPromptInput):

    def __init__(self, msg, confirm=False, help_string=None):
        super().__init__(msg=msg, help_string=help_string)
        self._confirm = confirm

    def __call__(self, *args, **kwargs):
        return prompt_pass(msg=self._msg, confirm=self._confirm, help_string=self._help_string)
