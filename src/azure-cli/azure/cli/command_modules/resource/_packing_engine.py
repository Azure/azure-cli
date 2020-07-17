# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from knack.util import CLIError
from azure.cli.core.util import get_file_json
from azure.cli.core.profiles import ResourceType, get_sdk


class PackagedTemplate():
    def __init__(self, template, artifacts):
        self.RootTemplate = template
        self.Artifacts = artifacts


class PackingContext():
    def __init__(self, root_template_directory):
        self.RootTemplateDirectory = os.path.abspath(root_template_directory)
        self.CurrentDirectory = os.path.abspath(root_template_directory)
        self.Artifact = []


# Packs the specified template and its referenced artifacts for use in a Template Spec.
# :param template_file: The path to the template spec .json file.
# :type name: str

def Pack(cmd, template_file):
    root_template_file_path = os.path.abspath(template_file)
    context = PackingContext(os.path.dirname(root_template_file_path))
    templateObj = get_file_json(template_file)
    PackArtifacts(cmd, root_template_file_path, context, templateObj)
    return PackagedTemplate(templateObj, getattr(context, 'Artifact'))

#  Recursively packs the specified template and its referenced artifacts and
#  adds the artifacts to the current packing context.

# :param template_abs_file_path: The path to the template spec .json file to pack.
# :type template_abs_file_path : str
# :param context : The packing context of the current packing operation
# :type content : PackingContext
# :param artifactableTemplateObj : The packagable template object
# :type artifactableTemplateObj : JSON


def PackArtifacts(cmd, template_abs_file_path, context, artifactableTemplateObj):
    originalDirectory = getattr(context, 'CurrentDirectory')
    try:
        context.CurrentDirectory = os.path.dirname(template_abs_file_path)
        templateLinktoArtifactObjs = GetTemplateLinksToArtifacts(cmd, artifactableTemplateObj, includeNested=True)

        for templateLinkObj in templateLinktoArtifactObjs:
            relativePath = str(templateLinkObj['relativePath'])
            if not relativePath:
                continue
            # This is a templateLink to a local template... Get the absolute path of the
            # template based on its relative path from the current template directory and
            # make sure it exists:

            absoluteLocalPath = os.path.join(getattr(context, 'CurrentDirectory'), relativePath)
            if not os.path.isfile(absoluteLocalPath):
                raise CLIError('File ' + absoluteLocalPath + 'not found.')

            # Let's make sure we're not referencing a file outside of our root directory
            # hierarchy. We won't allow such references for security purposes:

            if(not os.path.commonpath([getattr(context, 'RootTemplateDirectory')]) ==
               os.path.commonpath([getattr(context, 'RootTemplateDirectory'), absoluteLocalPath])):
                # TODO: Localize
                raise CLIError('Unable to handle the reference to file ' + absoluteLocalPath + 'from '
                               + template_abs_file_path + 'because it exists outside of the root template directory of '
                               + getattr(context, 'RootTemplateDirectory'))

            # Convert the template relative path to one that is relative to our root
            # directory path, and then if we haven't already processed that template into
            # an artifact elsewhere, we'll do so here...

            asRelativePath = AbsoluteToRelativePath(getattr(context, 'RootTemplateDirectory'), absoluteLocalPath)
            for prevAddedArtifact in getattr(context, 'Artifacts'):
                if os.path.samefile(getattr(prevAddedArtifact, 'path'), asRelativePath):
                    continue
            PackArtifacts(cmd, absoluteLocalPath, context, templateLinkObj)
            TemplateSpecTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                                   'TemplateSpecTemplateArtifact', mod='models')
            artifact = TemplateSpecTemplateArtifact(path=asRelativePath, template=templateLinkObj)
            context.Artifacts.append(artifact)
    finally:
        context.CurrentDirectory = originalDirectory


def GetDeploymentResourceObjects(cmd, templateObj, includeNested=False):
    immediateDeploymentResources = []
    for resource in templateObj['resources']:
        if str(resource['type']) is 'Microsoft.Resources/deployments':
            immediateDeploymentResources.append(resource)
    results = []
    for deploymentResourceObj in immediateDeploymentResources:
        results.append(deploymentResourceObj)
        DeploymentProperties = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                       'DeploymentProperties', mod='models')
        if(includeNested and 'properties' in deploymentResourceObj
           and isinstance(deploymentResourceObj['properties'], DeploymentProperties)):
            deploymentResourcePropsObj = deploymentResourceObj['properties']
            if 'template' in deploymentResourcePropsObj:
                results.extend(GetDeploymentResourceObjects(cmd, deploymentResourcePropsObj['template']))
    return results


def GetTemplateLinksToArtifacts(cmd, templateObj, includeNested=False):
    deploymentResourceObjs = GetDeploymentResourceObjects(templateObj, includeNested)
    templateLinkObjs = []
    DeploymentProperties, TemplateLink = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                                 'DeploymentProperties', 'TemplateLink', mod='models')
    for obj in deploymentResourceObjs:
        if('properties' in obj and isinstance(obj['properties'], DeploymentProperties)):
            propsObj = obj['properties']
            if('templateLink' in propsObj and isinstance(propsObj['templateLink'], TemplateLink)):
                templateLinkObj = propsObj['templateLink']
                if('relativePath' in templateLinkObj and isinstance(templateLinkObj, str)):
                    templateLinkObjs.append(templateLinkObj)
    return templateLinkObjs


def AbsoluteToRelativePath(rootDirectoryPath, absoluteFilePath):
    rootDirectoryPath = rootDirectoryPath.rstrip(os.sep)
    #Ensure we have a trailing seperator
    rootDirectoryPath += os.sep

    #AbsolutePath ensures paths are normalized
    filePath = os.path.abspath(absoluteFilePath)
    rootPath = os.path.abspath(rootDirectoryPath)
    relative_path = str(os.path.relpath(filePath, rootPath)).replace('/', os.sep)
    return relative_path
