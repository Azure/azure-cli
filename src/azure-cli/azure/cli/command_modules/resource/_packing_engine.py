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


def pack(cmd, template_file):
    """
    Packs the specified template and its referenced artifacts for use in a Template Spec.
    :param template_file: The path to the template spec .json file.
    :type name: str
    """
    root_template_file_path = os.path.abspath(template_file)
    context = PackingContext(os.path.dirname(root_template_file_path))
    template_content = read_file_content(template_file)
    sanitized_template = _remove_comments_from_json(template_content)
    template_json = json.loads(json.dumps(sanitized_template))
    _pack_artifacts(cmd, root_template_file_path, context)
    return PackagedTemplate(template_json, getattr(context, 'Artifact'))


def _pack_artifacts(cmd, template_abs_file_path, context):
    """
    Recursively packs the specified template and its referenced artifacts and
     adds the artifacts to the current packing context.

    :param template_abs_file_path: The path to the template spec .json file to pack.
    :type template_abs_file_path : str
    :param context : The packing context of the current packing operation
    :type content : PackingContext
    :param artifactableTemplateObj : The packagable template object
    :type artifactableTemplateObj : JSON
    """
    original_directory = getattr(context, 'CurrentDirectory')
    try:
        context.CurrentDirectory = os.path.dirname(template_abs_file_path)
        template_content = read_file_content(template_abs_file_path)
        artifactable_template_obj = sanitized_template = _remove_comments_from_json(template_content)
        template_json = json.loads(json.dumps(sanitized_template))
        template_link_to_artifact_objs = _get_template_links_to_artifacts(cmd, artifactable_template_obj, includeNested=True)

        for template_link_obj in template_link_to_artifact_objs:
            relative_path = str(template_link_obj['relative_path'])
            if not relative_path:
                continue
            # This is a templateLink to a local template... Get the absolute path of the
            # template based on its relative path from the current template directory and
            # make sure it exists:

            abs_local_path = os.path.join(getattr(context, 'CurrentDirectory'), relative_path)
            if not os.path.isfile(abs_local_path):
                raise CLIError('File ' + abs_local_path + 'not found.')

            # Let's make sure we're not referencing a file outside of our root directory
            # hierarchy. We won't allow such references for security purposes:

            if(not os.path.commonpath([getattr(context, 'RootTemplateDirectory')]) ==
               os.path.commonpath([getattr(context, 'RootTemplateDirectory'), abs_local_path])):
                raise CLIError('Unable to handle the reference to file ' + abs_local_path + 'from ' +
                               template_abs_file_path + 'because it exists outside of the root template directory of ' +
                               getattr(context, 'RootTemplateDirectory'))

            # Convert the template relative path to one that is relative to our root
            # directory path, and then if we haven't already processed that template into
            # an artifact elsewhere, we'll do so here...

            as_relative_path = _absolute_to_relative_path(getattr(context, 'RootTemplateDirectory'), abs_local_p ath)
            for prev_added_artifact in getattr(context, 'Artifact'):
                prev_added_artifact = os.path.join(getattr(context, 'RootTemplateDirectory'),
                                                 getattr(prev_added_artifact, 'path'))
                if os.path.samefile(prev_added_artifact, abs_local_path):
                    continue
            _pack_artifacts(cmd, abs_local_path, context)
            TemplateSpecTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                                   'TemplateSpecTemplateArtifact', mod='models')
            template_content = read_file_content(abs_local_path)
            sanitized_template = _remove_comments_from_json(template_content)
            template_json = json.loads(json.dumps(sanitized_template))
            artifact = TemplateSpecTemplateArtifact(path=as_relative_path, template=template_json)
            context.Artifact.append(artifact)
    finally:
        context.CurrentDirectory = original_directory


def _get_deployment_resource_objects(cmd, templateObj, includeNested=False):
    immediate_deployment_resources = []

    if 'resources' in templateObj:
        resources = templateObj['resources']
        for resource in resources:
            if (str(resource['type']) == 'Microsoft.Resources/deployments') is True:
                immediate_deployment_resources.append(resource)
    results = []
    for deployment_resource_obj in immediate_deployment_resources:
        results.append(deployment_resource_obj)
        if(includeNested and 'properties' in deployment_resource_obj):
            deployment_resource_props_obj = deployment_resource_obj['properties']
            if 'template' in deployment_resource_props_obj:
                results.extend(_get_deployment_resource_objects(cmd,
                                                                deployment_resource_props_obj['template'],
                                                                includeNested=True))
    return results


def _get_template_links_to_artifacts(cmd, templateObj, includeNested=False):
    deployment_resource_objs = _get_deployment_resource_objects(cmd, templateObj, includeNested)
    template_link_objs = []
    # TODO: Verify JSON Objects
    for obj in deployment_resource_objs:
        if 'properties' in obj:
            props_obj = obj['properties']
            if 'templateLink' in props_obj:
                template_link_obj = props_obj['templateLink']
                if 'relative_path' in template_link_obj:
                    template_link_objs.append(template_link_obj)
    return template_link_objs


def _absolute_to_relative_path(root_dir_path, abs_file_path):
    root_dir_path = root_dir_path.rstrip(os.sep)
    # Ensure we have a trailing seperator
    root_dir_path += os.sep
    # AbsolutePath ensures paths are normalized

    file_path = os.path.abspath(abs_file_path)
    root_path = os.path.abspath(root_dir_path)
    relative_path = str(os.path.relpath(file_path, root_path)).replace('/', os.sep)
    return relative_path


def unpack(cmd, exported_template, target_dir, template_file_name):

    packaged_template = PackagedTemplate(exported_template.template, exported_template.artifacts)
    # Ensure paths are normalized:
    template_file_name = os.path.basename(template_file_name)
    target_dir = os.path.abspath(target_dir).rstrip(os.sep)
    root_template_file_path = os.path.join(target_dir, template_file_name)

    # TODO: Directory/file existence checks..
    # Go through each artifact ad make sure it's not going to place artifacts
    # outside of the target directory:

    for artifact in getattr(packaged_template, 'Artifacts'):
        local_path = os.path.join(target_dir, getattr(artifact, 'path'))
        abs_local_path = os.path.abspath(local_path)
        if os.path.commonpath([target_dir]) != os.path.commonpath([target_dir, abs_local_path]):
            raise CLIError('Unable to unpack artifact ' + getattr(artifact, 'path') + 'because it would create a file' +
                           'outside of the target directory hierarchy of' + target_dir)

    # Now that the artifact paths checkout...let's begin by writing our main template
    # file and then processing each artifact:

    if not os.path.exists(target_dir):
        os.makedirs(os.path.dirname(target_dir))
    with open(root_template_file_path, 'w') as root_file:
        json.dump(getattr(packaged_template, 'RootTemplate'), root_file, indent=2)

    TemplateSpecTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                           'TemplateSpecTemplateArtifact', mod='models')
    for artifact in getattr(packaged_template, 'Artifacts'):
        if not isinstance(artifact, TemplateSpecTemplateArtifact):
            raise CLIError('Unknown artifact type encountered...')
        abs_local_path = os.path.abspath(os.path.join(target_dir, getattr(artifact, 'path')))
        if not os.path.exists(os.path.dirname(abs_local_path)):
            os.makedirs(os.path.dirname(abs_local_path))
        with open(abs_local_path, 'w') as artifact_file:
            json.dump(getattr(artifact, 'template'), artifact_file, indent=2)
    return target_dir
