# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import yaml
from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from .sdk.models import (
    Task,
    SourceRepositoryProperties,
    AgentProperties,
    TriggerProperties,
    SourceTrigger,
    BaseImageTrigger,
    SourceControlAuthInfo,
    PlatformProperties,
    SourceTriggerEvent,
    Architecture,
    Variant,
    DockerBuildStep,
    RunTaskStep,
    BuildTaskStep,
    TaskRunRequest,
    TaskUpdateParameters,
    SourceControlType
)
from ._utils import validate_managed_registry
from .build import acr_build_show_logs
from ._build_polling import get_build_with_polling


logger = get_logger(__name__)


TASK_NOT_SUPPORTED = 'Task is only supported for managed registries.'
DEFAULT_TOKEN_TYPE = 'PAT'


def acr_task_create(cmd,  # pylint: disable=too-many-locals
                    client,
                    task_name,
                    registry_name,
                    context_path=None,
                    image_names=None,
                    git_access_token=None,
                    status='Enabled',
                    os_type='Linux',
                    cpu=2,
                    timeout=3600,
                    docker_file=None,
                    definition_file=None,
                    values_file=None,
                    commit_trigger_enabled=True,
                    branch='master',
                    no_push=False,
                    no_cache=False,
                    arg=None,
                    secret_arg=None,
                    base_image_trigger='Runtime',
                    resource_group_name=None):

    if docker_file is None and definition_file is None and image_names is None:
        raise CLIError("One of --dockerfile or --definition-file argument is required")
    if docker_file is not None and definition_file is not None:
        raise CLIError("Cannot use both --dockerfile and --definition-file arguments to create a task")
    if docker_file is None and definition_file is None:
        yml_data = {'steps':[{'cmd': ', '.join(image_names)}]}
        acb_yml = yaml.dump(yml_data, default_flow_style=False, allow_unicode=True)
        print(acb_yml)
        step = RunTaskStep(
            task_definition_content=(base64.b64encode(acb_yml.encode())).decode('utf-8')
        )
        print(step.task_definition_content)
    if docker_file is not None:
        step = DockerBuildStep(
            image_names=image_names,
            is_push_enabled=not no_push,
            no_cache=no_cache,
            docker_file_path=docker_file,
            arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
            base_image_dependencies=[], #TODO
            context_path=context_path
        )
    if definition_file is not None:
        step = BuildTaskStep(
            definition_file_path=definition_file,
            values_file_path=values_file,
            context_path=context_path,
            arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
            base_image_dependencies=[], #TODO
        )

    registry, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    source_control_type = SourceControlType.visual_studio_team_service.value
    if context_path is not None and 'GITHUB.COM' in context_path.upper(): # TODO: remove github.com check?
        source_control_type = SourceControlType.github.value

    task_create_parameters = Task(
        location=registry.location,
        step=step,
        platform=PlatformProperties(
            os=os_type,
            architecture=Architecture.amd64.value
        ),
        status=status,
        timeout=timeout,
        agent_configuration=AgentProperties(
            cpu=cpu
        ),
        trigger=None if context_path is None else TriggerProperties(
            source_triggers=[
                SourceTrigger(
                    source_repository=SourceRepositoryProperties(
                        source_control_type=source_control_type,
                        repository_url=context_path,
                        branch=branch,
                        source_control_auth_properties=SourceControlAuthInfo(
                            token=git_access_token,
                            token_type=DEFAULT_TOKEN_TYPE,
                            refresh_token='',
                            scope='repo',
                            expires_in=1313141
                        )
                    ),
                    source_trigger_events=[SourceTriggerEvent.commit.value], #TODO
                    status="Enabled" if commit_trigger_enabled else "Disabled", #TODO
                    name="myTrigger" #TODO
                )
            ],
            base_image_trigger=BaseImageTrigger(
                base_image_trigger_type=base_image_trigger,
                status="Enabled", #TODO
                name="mybaseTrigger" #TODO
            )
        )
    )
    try:
        task = LongRunningOperation(cmd.cli_ctx)(
            client.create(resource_group_name=resource_group_name,
                          registry_name=registry_name,
                          task_name=task_name,
                          task_create_parameters=task_create_parameters))
    except ValidationError as e:
        raise CLIError(e)

    return task


def acr_task_show(cmd,
                  client,
                  task_name,
                  registry_name,
                  with_secure_properties=False,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    if not with_secure_properties:
        return client.get(resource_group_name, registry_name, task_name)
    else:
        return client.list_details(resource_group_name, registry_name, task_name)


def acr_task_list(cmd,
                  client,
                  registry_name,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_task_delete(cmd,
                    client,
                    task_name,
                    registry_name,
                    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, task_name)


def acr_task_update_get(client):  # pylint: disable=unused-argument
    """Returns an empty TaskUpdateParameters object.
    """
    return TaskUpdateParameters()


def acr_task_update_set(cmd,
                        client,
                        task_name,
                        registry_name,
                        resource_group_name=None,
                        parameters=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.update(resource_group_name, registry_name, task_name, parameters)

#TODO
def acr_task_update_custom(instance,  # pylint: disable=too-many-locals
                           status=None,
                           os_type=None,
                           cpu=None,
                           timeout=None,
                           context_path=None,
                           commit_trigger_enabled=None,
                           git_access_token=None,
                           branch=None,
                           image_names=None,
                           no_push=None,
                           no_cache=None,
                           docker_file=None,
                           definition_file=None,
                           values_file=None,
                           arg=None,
                           secret_arg=None,
                           base_image_trigger=None):
    if docker_file is None and definition_file is None:
        raise CLIError("One of --dockerfile or --definition-file argument is required")
    if docker_file is not None and definition_file is not None:
        raise CLIError("Cannot use both --dockerfile and --definition-file arguments to create a task")
    if docker_file is not None:
        instance.step = DockerBuildStep(
            image_names=image_names,
            is_push_enabled=not no_push,
            no_cache=no_cache,
            docker_file_path=docker_file,
            arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
            base_image_dependencies=[], #TODO
            context_path=context_path
        )
    if definition_file is not None:
        instance.step = BuildTaskStep(
            definition_file_path=definition_file,
            values_file_path=values_file,
            context_path=context_path,
            arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
            base_image_dependencies=[], #TODO
        )

    instance.platform = PlatformProperties(
        os=os_type,
        architecture=Architecture.amd64, #TODO
        variant=Variant.v8 #TODO
    )
    instance.status = status
    instance.timeout = timeout
    instance.agent_configuration = AgentProperties(
        cpu=cpu
    )
    instance.trigger = TriggerProperties(
        source_triggers=[
            SourceTrigger(
                source_repository=SourceRepositoryProperties(
                    source_control_type=None,
                    repository_url=context_path,
                    branch=branch,
                    source_control_auth_properties=SourceControlAuthInfo(
                        token=git_access_token,
                        token_type=DEFAULT_TOKEN_TYPE,
                        refresh_token='',
                        scope='repo',
                        expires_in=1313141
                    )
                ),
                source_trigger_events=[SourceTriggerEvent.commit, SourceTriggerEvent.pullrequest], #TODO
                status="Enabled" if commit_trigger_enabled else "Disabled", #TODO
                name="" #TODO
            )
        ],
        base_image_trigger=BaseImageTrigger(
            base_image_trigger_type=base_image_trigger,
            status="Enabled", #TODO
            name="" #TODO
        )
    )

    return instance


def acr_task_update_run(cmd,
                        client,
                        run_id,
                        registry_name,
                        no_archive=None,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    is_archive_enabled = not no_archive if no_archive is not None else None

    return client.update(resource_group_name=resource_group_name,
                         registry_name=registry_name,
                         run_id=run_id,
                         is_archive_enabled=is_archive_enabled)


def acr_task_run(cmd,
                 client,  # cf_acr_runs
                 task_name,
                 registry_name,
                 no_logs=False,
                 resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    from ._client_factory import cf_acr_registries_build
    client_registries = cf_acr_registries_build(cmd.cli_ctx)

    queued_run = LongRunningOperation(cmd.cli_ctx)(
        client_registries.schedule_run(resource_group_name,
                                       registry_name,
                                       TaskRunRequest(task_name=task_name)))

    run_id = queued_run.run_id
    logger.warning("Queued a run with run ID: %s", run_id)
    logger.warning("Waiting for run agent...")

    if no_logs:
        return get_build_with_polling(client, run_id, registry_name, resource_group_name)

    return acr_build_show_logs(client, run_id, registry_name, resource_group_name, True)


def acr_task_show_run(cmd,
                      client,  # cf_acr_runs
                      run_id,
                      registry_name,
                      resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, run_id)


#TODO
def acr_task_list_runs(cmd,
                       client,  # cf_acr_runs
                       registry_name,
                       top=15,
                       task_name=None,
                       run_status=None,
                       image=None,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    filter_str = None
    filter_str = _add_run_filter(filter_str, 'TaskName', task_name, 'eq')
    filter_str = _add_run_filter(filter_str, 'Status', run_status, 'eq')

    if image:
        from .repository import get_image_digest
        try:
            repository, _, manifest = get_image_digest(cmd.cli_ctx, registry_name, resource_group_name, image)
            filter_str = _add_run_filter(
                filter_str, 'OutputImageManifests', '{}@{}'.format(repository, manifest), 'contains')
        except CLIError as e:
            raise CLIError("Could not find image '{}'. {}".format(image, e))

    return client.list(resource_group_name, registry_name, filter=filter_str, top=top)


#TODO
def _add_run_filter(orig_filter, name, value, operator):
    if not value:
        return orig_filter

    if operator == 'contains':
        new_filter_str = "contains({}, '{}')".format(name, value)
    elif operator == 'eq':
        new_filter_str = "{} eq '{}'".format(name, value)
    else:
        raise ValueError("Allowed filter operator: {}".format(['contains', 'eq']))

    return "{} and {}".format(orig_filter, new_filter_str) if orig_filter else new_filter_str


def acr_task_logs(cmd,
                  client,  # cf_acr_runs
                  registry_name,
                  run_id=None,
                  task_name=None,
                  image=None,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    if not run_id:
        # show logs for the last run
        paged_runs = acr_task_list_runs(cmd,
                                        client,
                                        registry_name,
                                        top=1,
                                        task_name=task_name,
                                        image=image)
        try:
            run_id = paged_runs.get(0)[0].run_id
            logger.warning(_get_list_runs_message(base_message="Showing logs of the last created run",
                                                  task_name=task_name,
                                                  image=image))
            logger.warning("Run ID: %s", run_id)
        except (AttributeError, KeyError, TypeError, IndexError):
            raise CLIError(_get_list_runs_message(base_message="Could not find the last created run",
                                                  task_name=task_name,
                                                  image=image))

    return acr_build_show_logs(client, run_id, registry_name, resource_group_name)


def _get_list_runs_message(base_message, task_name=None, image=None):
    if task_name:
        base_message = "{} for task '{}'".format(base_message, task_name)
    if image:
        base_message = "{} for image '{}'".format(base_message, image)
    return "{}.".format(base_message)
