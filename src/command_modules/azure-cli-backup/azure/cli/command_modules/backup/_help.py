# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

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
            short-summary: Delete an existing Recovery Services vault.
            """

helps['backup vault list'] = """
            type: command
            short-summary: List Recovery Services vaults within a subscription.
            """

helps['backup vault show'] = """
            type: command
            short-summary: Show details of a Recovery Services vault.
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
            short-summary: Resoure which houses items or applications to be protected.
            """

helps['backup container list'] = """
            type: command
            short-summary: Lists the containers registered to the vault.
            """

helps['backup container show'] = """
            type: command
            short-summary: Show details of a container registered to a vault.
            """

helps['backup item'] = """
            type: group
            short-summary: An item which is already protected or backed up to Azure with an associated policy.
            """

helps['backup item list'] = """
            type: command
            short-summary: Lists all the backed up items within a container.
            """

helps['backup item show'] = """
            type: command
            short-summary: Shows details of a particular backed up item.
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
            short-summary: Get the default policy with default values to backup a VM. Define when you want to take backup and how long you want to retain each backup with policies.
            """

helps['backup policy list'] = """
            type: command
            short-summary: List all the policies for a Recovery services vault.
            """

helps['backup policy show'] = """
            type: command
            short-summary: Show the details of a policy.
            """

helps['backup policy delete'] = """
            type: command
            short-summary: Before you can delete a Backup protection policy, the policy must not have any associated Backup items. Before you delete the policy, make sure that each associated item is associated with some other policy. To associate another policy with a Backup item, use the set-policy command of the backup Item
            """

helps['backup policy set'] = """
            type: command
            short-summary: Update the properties of the backup policy. Use the show command to obtain a policy object. Modify the values of the object in a file and use this command to update.
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
            short-summary: Lists all the recovery points for the backed up item.
            """

helps['backup recoverypoint show'] = """
            type: command
            short-summary: Shows details of the recovery point.
            """

helps['backup protection'] = """
            type: group
            short-summary: Manage protection of your items, enable protection or disable it, or take on-demand backups.
            """

helps['backup protection enable-for-vm'] = """
            type: command
            short-summary: To start protecting the Azure VM as per the specified policy.
            """

helps['backup protection backup-now'] = """
            type: command
            short-summary: To perform an on-demand backup.
            """

helps['backup protection disable'] = """
            type: command
            short-summary: To stop protecting the backed up Item. Will ask for confirmation once again.
            """

helps['backup restore'] = """
            type: group
            short-summary: Restore the backed up items from recovery points in the Recovery Services vault.
            """

helps['backup restore disks'] = """
            type: command
            short-summary: Restore the disks of the backed VM from the specified recovery point.
            """

helps['backup restore files'] = """
            type: group
            short-summary: Gives access to all the files of the recovery point.
            """

helps['backup restore files mount-rp'] = """
            type: command
            short-summary: Downloads a script which mounts the files of a recovery point.
            """

helps['backup restore files unmount-rp'] = """
            type: command
            short-summary: Closes the access to the recovery point.
            """

helps['backup job'] = """
            type: group
            short-summary: Entity which contains the details of the job.
            """

helps['backup job list'] = """
            type: command
            short-summary: Lists all the backup jobs of the Recovery Services vault.
            """

helps['backup job show'] = """
            type: command
            short-summary: Show the details of a particular job.
            """

helps['backup job stop'] = """
            type: command
            short-summary: Suspend or terminate a currently running job.
            """

helps['backup job wait'] = """
            type: command
            short-summary: Wait until either the job completes or the specified timeout value is reached.
            """
