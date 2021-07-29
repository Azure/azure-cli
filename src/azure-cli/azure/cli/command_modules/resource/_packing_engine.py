# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import re
import json
from knack.util import CLIError
from azure.cli.core.azclierror import BadRequestError
from azure.cli.core.util import read_file_content, shell_safe_json_parse
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


# pylint: disable=redefined-outer-name
def process_template(template, preserve_order=True, file_path=None):
    from jsmin import jsmin

    # When commenting at the bottom of all elements in a JSON object, jsmin has a bug that will wrap lines.
    # It will affect the subsequent multi-line processing logic, so deal with this situation in advance here.
    template = re.sub(r'(^[\t ]*//[\s\S]*?\n)|(^[\t ]*/\*{1,2}[\s\S]*?\*/)', '', template, flags=re.M)
    minified = jsmin(template)

    # Remove extra spaces, compress multiline string(s)
    result = re.sub(r'\s\s+', ' ', minified, flags=re.DOTALL)

    try:
        return shell_safe_json_parse(result, preserve_order)
    except CLIError:
        # The processing of removing comments and compression will lead to misplacement of error location,
        # so the error message should be wrapped.
        if file_path:
            raise CLIError("Failed to parse '{}', please check whether it is a valid JSON format".format(file_path))
        raise CLIError("Failed to parse the JSON data, please check whether it is a valid JSON format")


def pack(cmd, template_file):
    """
    Packs the specified template and its referenced artifacts for use in a Template Spec.
    :param template_file: The path to the template spec .json file.
    :type name: str
    """
    root_template_file_path = os.path.abspath(template_file)
    context = PackingContext(os.path.dirname(root_template_file_path))
    template_content = read_file_content(template_file)
    template_json = json.loads(json.dumps(process_template(template_content)))
    _pack_artifacts(cmd, root_template_file_path, context)
    return PackagedTemplate(template_json, getattr(context, 'Artifact'))


def _pack_artifacts(cmd, template_abs_file_path, context):
    """
    Recursively packs the specified template and its referenced artifacts and
     adds the artifact(s) to the current packing context.

    :param template_abs_file_path: The path to the template spec .json file to pack.
    :type template_abs_file_path : str
    :param context : The packing context of the current packing operation
    :type content : PackingContext
    :param artifactableTemplateObj : The packageable template object
    :type artifactableTemplateObj : JSON
    """
    original_directory = getattr(context, 'CurrentDirectory')
    try:
        context.CurrentDirectory = os.path.dirname(template_abs_file_path)
        template_content = read_file_content(template_abs_file_path)
        artifactable_template_obj = _remove_comments_from_json(template_content)
        template_link_to_artifact_objs = _get_template_links_to_artifacts(cmd, artifactable_template_obj,
                                                                          includeNested=True)

        for template_link_obj in template_link_to_artifact_objs:
            relative_path = str(template_link_obj['relativePath'])
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
                raise BadRequestError('Unable to handle the reference to file ' + abs_local_path + 'from ' +
                                      template_abs_file_path +
                                      'because it exists outside of the root template directory of ' +
                                      getattr(context, 'RootTemplateDirectory'))

            # Convert the template relative path to one that is relative to our root
            # directory path, and then if we haven't already processed that template into
            # an artifact elsewhere, we'll do so here...

            as_relative_path = _absolute_to_relative_path(getattr(context, 'RootTemplateDirectory'), abs_local_path)
            for prev_added_artifact in getattr(context, 'Artifact'):
                prev_added_artifact = os.path.join(getattr(context, 'RootTemplateDirectory'),
                                                   getattr(prev_added_artifact, 'path'))
                if os.path.samefile(prev_added_artifact, abs_local_path):
                    continue
            _pack_artifacts(cmd, abs_local_path, context)
            LinkedTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                             'LinkedTemplateArtifact', mod='models')
            template_content = read_file_content(abs_local_path)
            template_json = json.loads(json.dumps(process_template(template_content)))
            artifact = LinkedTemplateArtifact(path=as_relative_path, template=template_json)
            context.Artifact.append(artifact)
    finally:
        context.CurrentDirectory = original_directory


def _get_deployment_resource_objects(cmd, template_obj, includeNested=False):
    immediate_deployment_resources = []

    if 'resources' in template_obj:
        resources = template_obj['resources']
        for resource in resources:
            if (str(resource['type']) == 'Microsoft.Resources/deployments') is True:
                immediate_deployment_resources.append(resource)
    results = []
    for deployment_resource_obj in immediate_deployment_resources:
        results.append(deployment_resource_obj)
        if(includeNested and 'properties' in deployment_resource_obj):
            deployment_resource_props_obj = deployment_resource_obj['properties']
            if 'mainTemplate' in deployment_resource_props_obj:
                results.extend(_get_deployment_resource_objects(cmd,
                                                                deployment_resource_props_obj['mainTemplate'],
                                                                includeNested=True))
    return results


def _get_template_links_to_artifacts(cmd, template_obj, includeNested=False):
    deployment_resource_objs = _get_deployment_resource_objects(cmd, template_obj, includeNested)
    template_link_objs = []
    # TODO: Verify JSON Objects
    for obj in deployment_resource_objs:
        if 'properties' in obj:
            props_obj = obj['properties']
            if 'templateLink' in props_obj:
                template_link_obj = props_obj['templateLink']
                if 'relativePath' in template_link_obj:
                    template_link_objs.append(template_link_obj)
    return template_link_objs


def _normalize_directory_seperators_for_local_file_system(abs_file_path):
    """
    Simply normalizes directory path separators in the specified path
    to match those of the local filesystem(s).
    """
    # Windows based:
    if os.sep == '\\':
        return str(abs_file_path).replace(os.altsep, '\\')
    # Unit/Other based:
    return str(abs_file_path).replace('\\', os.sep)


def _absolute_to_relative_path(root_dir_path, abs_file_path):
    root_dir_path = root_dir_path.rstrip(os.sep).rstrip(os.altsep)
    # Ensure we have a trailing seperator
    root_dir_path += os.sep
    # AbsolutePath ensures paths are normalized

    file_path = os.path.abspath(abs_file_path)
    root_path = os.path.abspath(root_dir_path)
    relative_path = str(os.path.relpath(file_path, root_path)).replace('/', os.sep)
    return relative_path


def unpack(cmd, exported_template, target_dir, template_file_name):

    packaged_template = PackagedTemplate(exported_template.main_template, exported_template.linked_templates)
    # Ensure paths are normalized:
    template_file_name = os.path.basename(template_file_name)
    target_dir = os.path.abspath(target_dir).rstrip(os.sep).rstrip(os.altsep)
    root_template_file_path = os.path.join(target_dir, template_file_name)

    # TODO: Directory/file existence checks..
    # Iterate through artifacts to ensure no artifact will be placed
    # outside of the target directory:

    artifacts = getattr(packaged_template, 'Artifacts')
    if artifacts is not None:
        for artifact in artifacts:
            local_path = os.path.join(target_dir,
                                      _normalize_directory_seperators_for_local_file_system(getattr(artifact, 'path')))
            abs_local_path = os.path.abspath(local_path)
            if os.path.commonpath([target_dir]) != os.path.commonpath([target_dir, abs_local_path]):
                raise BadRequestError('Unable to unpack linked template ' + getattr(artifact, 'path') +
                                      'because it would create a file outside of the target directory hierarchy of ' +
                                      target_dir)

        # Process each artifact:

        LinkedTemplateArtifact = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_TEMPLATESPECS,
                                         'LinkedTemplateArtifact', mod='models')
        for artifact in artifacts:
            if not isinstance(artifact, LinkedTemplateArtifact):
                raise CLIError('Unknown linked template type encountered...')
            artifact_path = _normalize_directory_seperators_for_local_file_system(getattr(artifact, 'path'))
            abs_local_path = os.path.abspath(os.path.join(target_dir, artifact_path))
            if not os.path.exists(os.path.dirname(abs_local_path)):
                os.makedirs(os.path.dirname(abs_local_path))
            with open(abs_local_path, 'w') as artifact_file:
                json.dump(getattr(artifact, 'template'), artifact_file, indent=2)

    # Write our main template file

    if not os.path.exists(target_dir):
        os.makedirs(os.path.dirname(target_dir))
    with open(root_template_file_path, 'w') as root_file:
        json.dump(getattr(packaged_template, 'RootTemplate'), root_file, indent=2)

    return target_dir
