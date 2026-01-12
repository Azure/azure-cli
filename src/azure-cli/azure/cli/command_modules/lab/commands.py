# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .validators import validate_claim_vm
from ._format import (transform_artifact_source_list, transform_artifact_source, transform_arm_template_list,
                      transform_arm_template, transform_vm_list, transform_vm, export_artifacts)


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # Virtual Machine Operations Commands
    with self.command_group('lab vm') as g:
        g.custom_command('claim', 'claim_vm', validator=validate_claim_vm)

    with self.command_group('lab vm'):
        from .custom import LabVmCreate, LabVmList, LabVmShow, LabVmDelete, LabVmStart, LabVmStop, \
            LabVmApplyArtifacts, LabVmHibernate
        self.command_table['lab vm create'] = LabVmCreate(loader=self)
        self.command_table['lab vm list'] = LabVmList(loader=self, table_transformer=transform_vm_list)
        self.command_table['lab vm show'] = LabVmShow(loader=self, table_transformer=transform_vm)
        self.command_table['lab vm delete'] = LabVmDelete(loader=self)
        self.command_table['lab vm start'] = LabVmStart(loader=self)
        self.command_table['lab vm stop'] = LabVmStop(loader=self)
        self.command_table['lab vm hibernate'] = LabVmHibernate(loader=self)
        self.command_table['lab vm apply-artifacts'] = LabVmApplyArtifacts(loader=self)

    # Lab Operations Commands
    with self.command_group('lab'):
        from .custom import LabGet, LabDelete
        self.command_table['lab get'] = LabGet(loader=self)
        self.command_table['lab delete'] = LabDelete(loader=self)

    # Custom Image Operations Commands
    with self.command_group('lab custom-image'):
        from .custom import CustomImageCreate, CustomImageShow, CustomImageDelete
        self.command_table['lab custom-image create'] = CustomImageCreate(loader=self)
        self.command_table['lab custom-image show'] = CustomImageShow(loader=self)
        self.command_table['lab custom-image delete'] = CustomImageDelete(loader=self)

    # Artifact Source Operations Commands
    with self.command_group('lab artifact-source'):
        from .aaz.latest.lab.artifact_source import List
        from .custom import ArtifactSourceShow
        self.command_table['lab artifact-source list'] = List(loader=self,
                                                              table_transformer=transform_artifact_source_list)
        self.command_table['lab artifact-source show'] = ArtifactSourceShow(loader=self,
                                                                            table_transformer=transform_artifact_source)

    # Virtual Network Operations Commands
    with self.command_group('lab vnet'):
        from .custom import LabVnetGet
        self.command_table['lab vnet get'] = LabVnetGet(loader=self)

    # Formula Operations Commands
    with self.command_group('lab formula'):
        from .custom import FormulaShow, FormulaDelete, FormulaExportArtifacts
        self.command_table['lab formula show'] = FormulaShow(loader=self)
        self.command_table['lab formula export-artifacts'] = FormulaExportArtifacts(loader=self,
                                                                                    table_transformer=export_artifacts)
        self.command_table['lab formula delete'] = FormulaDelete(loader=self)

    # Secret Operations Commands
    with self.command_group('lab secret'):
        from .custom import SecretSet, SecretList, SecretShow, SecretDelete
        self.command_table['lab secret set'] = SecretSet(loader=self)
        self.command_table['lab secret list'] = SecretList(loader=self)
        self.command_table['lab secret show'] = SecretShow(loader=self)
        self.command_table['lab secret delete'] = SecretDelete(loader=self)

    # Environment Operations Commands
    with self.command_group('lab environment'):
        from .custom import EnvironmentCreate, EnvironmentList, EnvironmentShow, EnvironmentDelete
        self.command_table['lab environment create'] = EnvironmentCreate(loader=self)
        self.command_table['lab environment list'] = EnvironmentList(loader=self)
        self.command_table['lab environment show'] = EnvironmentShow(loader=self)
        self.command_table['lab environment delete'] = EnvironmentDelete(loader=self)

    # ARM Templates Operations Commands
    with self.command_group('lab arm-template'):
        from .aaz.latest.lab.arm_template import List
        from .custom import ArmTemplateShow
        self.command_table['lab arm-template list'] = List(loader=self, table_transformer=transform_arm_template_list)
        self.command_table['lab arm-template show'] = ArmTemplateShow(loader=self,
                                                                      table_transformer=transform_arm_template)

    with self.command_group('lab', is_preview=True):
        pass
