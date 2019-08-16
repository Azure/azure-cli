# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['dms'] = """
type: group
short-summary: Manage Azure Data Migration Service (DMS) instances.
"""

helps['dms check-name'] = """
type: command
short-summary: Check if a given DMS instance name is available in a given region as well as the name's validity.
parameters:
  - name: --name -n
    type: string
    short-summary: >
        The Service name to check.
"""

helps['dms check-status'] = """
type: command
short-summary: Perform a health check and return the status of the service and virtual machine size.
"""

helps['dms delete'] = """
type: command
short-summary: Delete an instance of the Data Migration Service.
parameters:
  - name: --delete-running-tasks
    type: bool
    short-summary: >
        Cancel any running tasks before deleting the service.
"""

helps['dms list'] = """
type: command
short-summary: List the DMS instances within your currently configured subscription (to set this use "az account set"). If provided, only show the instances within a given resource group.
examples:
  - name: List all the instances in your subscription.
    text: >
        az dms list
  - name: List all the instances in a given resource group.
    text: >
        az dms list -g myresourcegroup
"""

helps['dms list-skus'] = """
type: command
short-summary: List the SKUs that are supported by the Data Migration Service.
"""

helps['dms project'] = """
type: group
short-summary: Manage Projects for an instance of the Data Migration Service.
"""

helps['dms project check-name'] = """
type: command
short-summary: Check if a given Project name is available within a given instance of DMS as well as the name's validity.
parameters:
  - name: --name -n
    type: string
    short-summary: >
        The Project name to check.
"""

helps['dms project delete'] = """
type: command
short-summary: Delete a Project.
parameters:
  - name: --delete-running-tasks
    type: bool
    short-summary: >
        Cancel any running tasks before deleting the Project.
"""

helps['dms project list'] = """
type: command
short-summary: List the Projects within an instance of DMS.
"""

helps['dms project show'] = """
type: command
short-summary: Show the details of a migration Project.
"""

helps['dms project task'] = """
type: group
short-summary: Manage Tasks for a Data Migration Service instance's Project.
"""

helps['dms project task cancel'] = """
type: command
short-summary: Cancel a Task if it's currently queued or running.
"""

helps['dms project task check-name'] = """
type: command
short-summary: Check if a given Task name is available within a given instance of DMS as well as the name's validity.
parameters:
  - name: --name -n
    type: string
    short-summary: >
        The Task name to check.
"""

helps['dms project task delete'] = """
type: command
short-summary: Delete a migration Task.
parameters:
  - name: --delete-running-tasks
    type: bool
    short-summary: >
        If the Task is currently running, cancel the Task before deleting the Project.
"""

helps['dms project task list'] = """
type: command
short-summary: List the Tasks within a Project. Some tasks may have a status of Unknown, which indicates that an error occurred while querying the status of that task.
parameters:
  - name: --task-type
    type: string
    short-summary: >
        Filters the list by the type of task. For the list of possible types see "az dms check-status".
examples:
  - name: List all Tasks within a Project.
    text: >
        az dms project task list --project-name myproject -g myresourcegroup --service-name mydms
  - name: List only the SQL to SQL migration tasks within a Project.
    text: >
        az dms project task list --project-name myproject -g myresourcegroup --service-name mydms --task-type Migrate.SqlServer.SqlDb
"""

helps['dms project task show'] = """
type: command
short-summary: Show the details of a migration Task. Use the "--expand" to get more details.
parameters:
  - name: --expand
    type: string
    short-summary: >
        Expand the response to provide more details. Use with "command" to see more details of the Task.
        Use with "output" to see the results of the Task's migration.
"""

helps['dms show'] = """
type: command
short-summary: Show the details for an instance of the Data Migration Service.
"""

helps['dms start'] = """
type: command
short-summary: Start an instance of the Data Migration Service. It can then be used to run data migrations.
"""

helps['dms stop'] = """
type: command
short-summary: Stop an instance of the Data Migration Service. While stopped, it can't be used to run data migrations and the owner won't be billed.
"""

helps['dms wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the DMS instance is met.
"""
