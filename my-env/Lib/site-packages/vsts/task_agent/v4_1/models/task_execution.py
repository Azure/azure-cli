# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskExecution(Model):
    """TaskExecution.

    :param exec_task: The utility task to run.  Specifying this means that this task definition is simply a meta task to call another task. This is useful for tasks that call utility tasks like powershell and commandline
    :type exec_task: :class:`TaskReference <task-agent.v4_1.models.TaskReference>`
    :param platform_instructions: If a task is going to run code, then this provides the type/script etc... information by platform. For example, it might look like. net45: { typeName: "Microsoft.TeamFoundation.Automation.Tasks.PowerShellTask", assemblyName: "Microsoft.TeamFoundation.Automation.Tasks.PowerShell.dll" } net20: { typeName: "Microsoft.TeamFoundation.Automation.Tasks.PowerShellTask", assemblyName: "Microsoft.TeamFoundation.Automation.Tasks.PowerShell.dll" } java: { jar: "powershelltask.tasks.automation.teamfoundation.microsoft.com", } node: { script: "powershellhost.js", }
    :type platform_instructions: dict
    """

    _attribute_map = {
        'exec_task': {'key': 'execTask', 'type': 'TaskReference'},
        'platform_instructions': {'key': 'platformInstructions', 'type': '{{str}}'}
    }

    def __init__(self, exec_task=None, platform_instructions=None):
        super(TaskExecution, self).__init__()
        self.exec_task = exec_task
        self.platform_instructions = platform_instructions
