# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import json
from knack.util import CLIError
from azure.cli.core.util import read_file_content
from azure.cli.command_modules.resource.custom import _remove_comments_from_json
from azure.cli.core.profiles import ResourceType, get_sdk


class PackagedTemplate():  # pylint: disable=too-few-public-methods
    def __init__(self, template, artifacts):
        self.RootTemplate = template
        self.Artifacts = artifacts


class PackingContext():  # pylint: disable=too-few-public-methods
    def __init__(self, root_template_directory):
        self.RootTemplateDirectory = os.path.abspath(root_template_directory)
        self.CurrentDirectory = os.path.abspath(root_template_directory)
        self.Artifact = []


# Packs the specified template and its referenced artifacts for use in a Template Spec.
# :param template_file: The path to the template spec .json file.
# :type name: str

def pack(cmd, template_file):
    root_template_file_path = os.path.abspath(template_file)
    context = PackingContext(os.path.dirname(root_template_file_path))
    template_content = read_file_content(template_file)
    sanitized_template = _remove_comments_from_json(template_content)
    template_json = json.loads(json.dumps(sanitized_template))
    _pack_artifacts(cmd, root_template_file_path, context)
    return PackagedTemplate(template_json, getattr(context, 'Artifact'))

#  Recursively packs the specified template and its referenced artifacts and
#  adds the artifacts to the current packing context.

# :param template_abs_file_path: The path to the template spec .json file to pack.
# :type template_abs_file_path : str
# :param context : The packing context of the current packing operation
# :type content : PackingContext
# :param artifactableTemplateObj : The packagable template object
# :type artifactableTemplateObj : JSON


def _pack_artifacts(cmd, template_abs_file_path, context):
    originalDirectory = getattr(context, 'CurrentDirectory')
    try:
        context.CurrentDirectory = os.path.dirname(template_abs_file_path)
        template_content = read_file_content(template_abs_file_path)
        artifactableTemplateObj = sanitized_template = _remove_comments_from_json(template_content)
        template_json = json.loads(json.dumps(sanitized_template))
        templateLinktoArtifactObjs = _get_template_links_to_artifacts(cmd, artifactableTemplateObj, includeNested=True)

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
                raise CLIError('Unable to handle the reference to file ' + absoluteLocalPath + 'from ' +
                               template_abs_file_path + 'because it exists outside of the root template directory of ' +
                               getattr(context, 'RootTemplateDirectory'))

            # Convert the template relative path to one that is relative to our root
            # directory path, and then if we haven't already processed that template into
            # an artifact elsewhere, we'll do so here...

            asRelativePath = _absolute_to_relative_path(getattr(context, 'RootTemplateDirectory'), absoluteLocalPath)
            for prevAddedArtifact in getattr(context, 'Artifact'):
                prevAddedArtifact = os.path.join(getattr(context, 'RootTemplateDirectory'),
                                                 getattr(prevAddedArtifact, 'path'))
                if os.path.samefile(prevAddedArtifact, absoluteLocalPath):
                    continue
            _pack_artifacts(cmd, absoluteLocalPath, context)
            TemplateSpecTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                                   'TemplateSpecTemplateArtifact', mod='models')
            template_content = read_file_content(absoluteLocalPath)
            sanitized_template = _remove_comments_from_json(template_content)
            template_json = json.loads(json.dumps(sanitized_template))
            artifact = TemplateSpecTemplateArtifact(path=asRelativePath, template=template_json)
            context.Artifact.append(artifact)
    finally:
        context.CurrentDirectory = originalDirectory


def _get_deployment_resource_objects(cmd, templateObj, includeNested=False):
    immediateDeploymentResources = []

    if 'resources' in templateObj:
        resources = templateObj['resources']
        for resource in resources:
            if (str(resource['type']) == 'Microsoft.Resources/deployments') is True:
                immediateDeploymentResources.append(resource)
    results = []
    for deploymentResourceObj in immediateDeploymentResources:
        results.append(deploymentResourceObj)
        if(includeNested and 'properties' in deploymentResourceObj):
            deploymentResourcePropsObj = deploymentResourceObj['properties']
            if 'template' in deploymentResourcePropsObj:
                results.extend(_get_deployment_resource_objects(cmd,
                                                                deploymentResourcePropsObj['template'],
                                                                includeNested=True))
    return results


def _get_template_links_to_artifacts(cmd, templateObj, includeNested=False):
    deploymentResourceObjs = _get_deployment_resource_objects(cmd, templateObj, includeNested)
    templateLinkObjs = []
    # TODO: Verify JSON Objects
    for obj in deploymentResourceObjs:
        if 'properties' in obj:
            propsObj = obj['properties']
            if 'templateLink' in propsObj:
                templateLinkObj = propsObj['templateLink']
                if 'relativePath' in templateLinkObj:
                    templateLinkObjs.append(templateLinkObj)
    return templateLinkObjs


def _absolute_to_relative_path(rootDirectoryPath, absoluteFilePath):
    rootDirectoryPath = rootDirectoryPath.rstrip(os.sep)
    # Ensure we have a trailing seperator
    rootDirectoryPath += os.sep
    # AbsolutePath ensures paths are normalized

    filePath = os.path.abspath(absoluteFilePath)
    rootPath = os.path.abspath(rootDirectoryPath)
    relative_path = str(os.path.relpath(filePath, rootPath)).replace('/', os.sep)
    return relative_path


def unpack(cmd, exported_template, targetDirectory, templateFileName):

    packagedTemplate = PackagedTemplate(exported_template.template, exported_template.artifacts)
    # Ensure paths are normalized:
    templateFileName = os.path.basename(templateFileName)
    targetDirectory = os.path.abspath(targetDirectory).rstrip(os.sep)
    rootTemplateFilePath = os.path.join(targetDirectory, templateFileName)

    # TODO: Directory/file existence checks..
    # Go through each artifact ad make sure it's not going to place artifacts
    # outside of the target directory:

    for artifact in getattr(packagedTemplate, 'Artifacts'):
        localPath = os.path.join(targetDirectory, getattr(artifact, 'path'))
        absLocalPath = os.path.abspath(localPath)
        if os.path.commonpath([targetDirectory]) != os.path.commonpath([targetDirectory, absLocalPath]):
            raise CLIError('Unable to unpack artifact ' + getattr(artifact, 'path') + 'because it would create a file' +
                           'outside of the target directory hierarchy of' + targetDirectory)

    # Now that the artifact paths checkout...let's begin by writing our main template
    # file and then processing each artifact:

    if not os.path.exists(targetDirectory):
        os.makedirs(os.path.dirname(targetDirectory))
    with open(rootTemplateFilePath, 'w') as rootFile:
        json.dump(getattr(packagedTemplate, 'RootTemplate'), rootFile, indent=2)

    TemplateSpecTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                           'TemplateSpecTemplateArtifact', mod='models')
    for artifact in getattr(packagedTemplate, 'Artifacts'):
        if not isinstance(artifact, TemplateSpecTemplateArtifact):
            raise CLIError('Unknown artifact type encountered...')
        absoluteLocalPath = os.path.abspath(os.path.join(targetDirectory, getattr(artifact, 'path')))
        if not os.path.exists(os.path.dirname(absoluteLocalPath)):
            os.makedirs(os.path.dirname(absoluteLocalPath))
        with open(absoluteLocalPath, 'w') as artifactFile:
            json.dump(getattr(artifact, 'template'), artifactFile, indent=2)
    return targetDirectory
