# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['backup'] = """
            type: group
            short-summary: Commands to manage Azure Backups.
            """

helps['backup vault'] = """
            type: group
            short-summary: Online storage entity in Azure used to hold data such as backup copies, recovery points and backup policies.
            """

helps['backup vault create'] = """
            type: command
            short-summary: Create a new Recovery Services vault.
            """

helps['backup vault delete'] = """
            type: command
            short-summary: Delete an existing Recovery services vault.
            """

helps['backup vault list'] = """
            type: command
            short-summary: List Recovery service vaults within a subscription.
            """

helps['backup vault show'] = """
            type: command
            short-summary: Show details of a particular Recovery service vault.
            """

helps['backup vault backup-properties'] = """
            type: group
            short-summary: Properties of the Recovery Services vault.
            """

helps['backup vault backup-properties show'] = """
            type: command
            short-summary: Gets backup related properties of the Recovery Services vault.
            """

helps['backup vault backup-properties set'] = """
            type: command
            short-summary: Sets backup related properties of the Recovery Services vault.
            """

helps['backup container'] = """
            type: group
            short-summary: Resource which houses items or applications to be protected.
            """

helps['backup container list'] = """
            type: command
            short-summary: List containers registered to a Recovery services vault.
            """

helps['backup container show'] = """
            type: command
            short-summary: Show details of a container registered to a Recovery services vault.
            """

helps['backup item'] = """
            type: group
            short-summary: An item which is already protected or backed up to an Azure Recovery services vault with an associated policy.
            """

helps['backup item list'] = """
            type: command
            short-summary: List all backed up items within a container.
            """

helps['backup item show'] = """
            type: command
            short-summary: Show details of a particular backed up item.
            """

helps['backup item set-policy'] = """
            type: command
            short-summary: Update the policy associated with this item.
            """

helps['backup policy'] = """
            type: group
            short-summary: A backup policy defines when you want to take a backup and for how long you would retain each backup copy.
            """

helps['backup policy get-default-for-vm'] = """
            type: command
            short-summary: Get the default policy with default values to backup a VM.
            """

helps['backup policy list'] = """
            type: command
            short-summary: List all policies for a Recovery services vault.
            """

helps['backup policy show'] = """
            type: command
            short-summary: Show details of a particular policy.
            """

helps['backup policy delete'] = """
            type: command
            short-summary: Before you can delete a Backup protection policy, the policy must not have any associated Backup items. To  associate another policy with a Backup item, use the backup item set-policy command.
            """

helps['backup policy set'] = """
            type: command
            short-summary: Update the properties of the backup policy.
            """

helps['backup policy list-associated-items'] = """
            type: command
            short-summary: List all items protected by a backup policy.
            """

helps['backup recoverypoint'] = """
            type: group
            short-summary: A snapshot of data at that point-of-time, stored in Recovery Services Vault, from which you can restore information.
            """

helps['backup recoverypoint list'] = """
            type: command
            short-summary: List all recovery points of a backed up item.
            """

helps['backup recoverypoint show'] = """
            type: command
            short-summary: Shows details of a particular recovery point.
            """

helps['backup protection'] = """
            type: group
            short-summary: Manage protection of your items, enable protection or disable it, or take on-demand backups.
            """

helps['backup protection enable-for-vm'] = """
            type: command
            short-summary: Start protecting a previously unprotected Azure VM as per the specified policy to a Recovery services vault.
            """

helps['backup protection backup-now'] = """
            type: command
            short-summary: Perform an on-demand backup of a backed up item.
            """

helps['backup protection disable'] = """
            type: command
            short-summary: Stop protecting a backed up Azure VM.
            """

helps['backup restore'] = """
            type: group
            short-summary: Restore backed up items from recovery points in a Recovery Services vault.
            """

helps['backup restore restore-disks'] = """
            type: command
            short-summary: Restore disks of the backed VM from the specified recovery point.
            """

helps['backup restore files'] = """
            type: group
            short-summary: Gives access to all files of a recovery point.
            """

helps['backup restore files mount-rp'] = """
            type: command
            short-summary: Download a script which mounts files of a recovery point.
            """

helps['backup restore files unmount-rp'] = """
            type: command
            short-summary: Close access to the recovery point.
            """

helps['backup job'] = """
            type: group
            short-summary: Entity which contains details of the job.
            """

helps['backup job list'] = """
            type: command
            short-summary: List all backup jobs of a Recovery Services vault.
            """

helps['backup job show'] = """
            type: command
            short-summary: Show details of a particular job.
            """

helps['backup job stop'] = """
            type: command
            short-summary: Suspend or terminate a currently running job.
            """

helps['backup job wait'] = """
            type: command
            short-summary: Wait until either the job completes or the specified timeout value is reached.
            """
