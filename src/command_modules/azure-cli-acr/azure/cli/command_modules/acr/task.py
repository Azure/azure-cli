# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from ._utils import (
    get_registry_by_name,
    validate_managed_registry,
    get_validate_platform,
    get_custom_registry_credentials,
    get_yaml_and_values
)
from ._stream_utils import stream_logs

logger = get_logger(__name__)


TASK_NOT_SUPPORTED = 'Task is only supported for managed registries.'
DEFAULT_TOKEN_TYPE = 'PAT'
NULL_CONTEXT = '/dev/null'
IDENTITY_LOCAL_ID = '[system]'
IDENTITY_GLOBAL_REMOVE = '[all]'

DEFAULT_TIMEOUT_IN_SEC = 60 * 60  # 60 minutes
DEFAULT_CPU = 2
ALLOWED_TASK_FILE_TYPES = ('.yaml', '.yml', '.toml', '.json', '.sh', '.bash', '.zsh', '.ps1',
                           '.ps', '.cmd', '.bat', '.ts', '.js', '.php', '.py', '.rb', '.lua')


def acr_task_create(cmd,  # pylint: disable=too-many-locals
                    client,
                    task_name,
                    registry_name,
                    context_path,
                    file=None,
                    cmd_value=None,
                    git_access_token=None,
                    image_names=None,
                    status='Enabled',
                    platform=None,
                    cpu=DEFAULT_CPU,
                    timeout=DEFAULT_TIMEOUT_IN_SEC,
                    values=None,
                    source_trigger_name='defaultSourceTriggerName',
                    commit_trigger_enabled=True,
                    pull_request_trigger_enabled=True,
                    branch='master',
                    no_push=False,
                    no_cache=False,
                    arg=None,
                    secret_arg=None,
                    set_value=None,
                    set_secret=None,
                    base_image_trigger_name='defaultBaseimageTriggerName',
                    base_image_trigger_enabled=True,
                    base_image_trigger_type='Runtime',
                    resource_group_name=None,
                    assign_identity=None,
                    target=None,
                    auth_mode=None):

    registry, resource_group_name = get_registry_by_name(
        cmd.cli_ctx, registry_name, resource_group_name)

    if context_path.lower() == NULL_CONTEXT:
        context_path = None
        commit_trigger_enabled = False
        pull_request_trigger_enabled = False

    if (commit_trigger_enabled or pull_request_trigger_enabled) and not git_access_token:
        raise CLIError("If source control trigger is enabled [--commit-trigger-enabled] or "
                       "[--pull-request-trigger-enabled] --git-access-token must be provided.")

    if cmd_value and file:
        raise CLIError(
            "Task can be created with either "
            "--cmd myCommand -c /dev/null or "
            "-f myFile -c myContext, but not both.")

    if context_path:
        if file.endswith(ALLOWED_TASK_FILE_TYPES):
            FileTaskStep = cmd.get_models('FileTaskStep')
            step = FileTaskStep(
                task_file_path=file,
                values_file_path=values,
                context_path=context_path,
                context_access_token=git_access_token,
                values=(set_value if set_value else []) + (set_secret if set_secret else [])
            )
        else:
            DockerBuildStep = cmd.get_models('DockerBuildStep')
            step = DockerBuildStep(
                image_names=image_names,
                is_push_enabled=not no_push,
                no_cache=no_cache,
                docker_file_path=file,
                arguments=(arg if arg else []) + (secret_arg if secret_arg else []),
                context_path=context_path,
                context_access_token=git_access_token,
                target=target
            )
    else:
        yaml_template, values_content = get_yaml_and_values(
            cmd_value, timeout, file)
        import base64
        EncodedTaskStep = cmd.get_models('EncodedTaskStep')
        step = EncodedTaskStep(
            encoded_task_content=base64.b64encode(
                yaml_template.encode()).decode(),
            encoded_values_content=base64.b64encode(
                values_content.encode()).decode(),
            context_path=context_path,
            context_access_token=git_access_token,
            values=(set_value if set_value else []) + (set_secret if set_secret else [])
        )

    SourceControlType, SourceTriggerEvent = cmd.get_models(
        'SourceControlType', 'SourceTriggerEvent')
    source_control_type = SourceControlType.visual_studio_team_service.value
    if context_path is not None and 'GITHUB.COM' in context_path.upper():
        source_control_type = SourceControlType.github.value

    source_triggers = None
    source_trigger_events = []
    if commit_trigger_enabled:
        source_trigger_events.append(SourceTriggerEvent.commit.value)
    if pull_request_trigger_enabled:
        source_trigger_events.append(SourceTriggerEvent.pullrequest.value)
    # if source_trigger_events contains any event types we assume they are enabled
    if source_trigger_events:
        SourceTrigger, SourceProperties, AuthInfo, TriggerStatus = cmd.get_models(
            'SourceTrigger', 'SourceProperties', 'AuthInfo', 'TriggerStatus')
        source_triggers = [
            SourceTrigger(
                source_repository=SourceProperties(
                    source_control_type=source_control_type,
                    repository_url=context_path,
                    branch=branch,
                    source_control_auth_properties=AuthInfo(
                        token=git_access_token,
                        token_type=DEFAULT_TOKEN_TYPE,
                        scope='repo'
                    )
                ),
                source_trigger_events=source_trigger_events,
                status=TriggerStatus.enabled.value,
                name=source_trigger_name
            )
        ]

    base_image_trigger = None
    if base_image_trigger_enabled:
        BaseImageTrigger, TriggerStatus = cmd.get_models(
            'BaseImageTrigger', 'TriggerStatus')
        base_image_trigger = BaseImageTrigger(
            base_image_trigger_type=base_image_trigger_type,
            status=TriggerStatus.enabled.value if base_image_trigger_enabled else TriggerStatus.disabled.value,
            name=base_image_trigger_name
        )

    platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)

    Task, PlatformProperties, AgentProperties, TriggerProperties = cmd.get_models(
        'Task', 'PlatformProperties', 'AgentProperties', 'TriggerProperties')

    identity = None
    if assign_identity is not None:
        identity = _build_identities_info(cmd, assign_identity)

    task_create_parameters = Task(
        identity=identity,
        location=registry.location,
        step=step,
        platform=PlatformProperties(
            os=platform_os,
            architecture=platform_arch,
            variant=platform_variant
        ),
        status=status,
        timeout=timeout,
        agent_configuration=AgentProperties(
            cpu=cpu
        ),
        trigger=TriggerProperties(
            source_triggers=source_triggers,
            base_image_trigger=base_image_trigger
        ),
        credentials=get_custom_registry_credentials(
            cmd=cmd,
            auth_mode=auth_mode
        )
    )

    try:
        return client.create(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             task_name=task_name,
                             task_create_parameters=task_create_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_task_show(cmd,
                  client,
                  task_name,
                  registry_name,
                  with_secure_properties=False,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    if with_secure_properties:
        return client.get_details(resource_group_name, registry_name, task_name)
    return client.get(resource_group_name, registry_name, task_name)


def acr_task_list(cmd,
                  client,
                  registry_name,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_task_delete(cmd,
                    client,
                    task_name,
                    registry_name,
                    resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, task_name)


def acr_task_update(cmd,  # pylint: disable=too-many-locals
                    client,
                    task_name,
                    registry_name,
                    resource_group_name=None,
                    # task parameters
                    status=None,
                    platform=None,
                    cpu=None,
                    timeout=None,
                    context_path=None,
                    commit_trigger_enabled=None,
                    pull_request_trigger_enabled=None,
                    git_access_token=None,
                    branch=None,
                    image_names=None,
                    no_push=None,
                    no_cache=None,
                    file=None,
                    values=None,
                    arg=None,
                    secret_arg=None,
                    set_value=None,
                    set_secret=None,
                    base_image_trigger_enabled=None,
                    base_image_trigger_type=None,
                    target=None,
                    auth_mode=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    task = client.get(resource_group_name, registry_name, task_name)
    step = task.step

    arguments = _get_all_override_arguments(arg, secret_arg)
    set_values = _get_all_override_arguments(set_value, set_secret)

    FileTaskStepUpdateParameters, DockerBuildStepUpdateParameters = cmd.get_models(
        'FileTaskStepUpdateParameters', 'DockerBuildStepUpdateParameters')
    if file and file.endswith(ALLOWED_TASK_FILE_TYPES):
        step = FileTaskStepUpdateParameters(
            task_file_path=file,
            values_file_path=values,
            context_path=context_path,
            context_access_token=git_access_token,
            values=set_values
        )
    elif file and not file.endswith(ALLOWED_TASK_FILE_TYPES):
        step = DockerBuildStepUpdateParameters(
            image_names=image_names,
            is_push_enabled=not no_push,
            no_cache=no_cache,
            docker_file_path=file,
            arguments=arguments,
            context_path=context_path,
            context_access_token=git_access_token,
            target=target
        )
    elif step:
        DockerBuildStep, FileTaskStep = cmd.get_models(
            'DockerBuildStep', 'FileTaskStep')
        if isinstance(step, DockerBuildStep):
            step = DockerBuildStepUpdateParameters(
                image_names=image_names,
                is_push_enabled=not no_push,
                no_cache=no_cache,
                docker_file_path=file,
                arguments=arguments,
                context_path=context_path,
                context_access_token=git_access_token,
                target=target
            )

        elif isinstance(step, FileTaskStep):
            step = FileTaskStepUpdateParameters(
                task_file_path=file,
                values_file_path=values,
                context_path=context_path,
                context_access_token=git_access_token,
                values=set_values
            )

    source_control_type = None
    if context_path:
        SourceControlType = cmd.get_models('SourceControlType')
        if 'GITHUB.COM' in context_path.upper():
            source_control_type = SourceControlType.github.value
        else:
            source_control_type = SourceControlType.visual_studio_team_service.value

    # update trigger
    source_trigger_update_params, base_image_trigger_update_params = None, None
    if task.trigger:
        TriggerStatus = cmd.get_models('TriggerStatus')

        source_triggers = task.trigger.source_triggers
        base_image_trigger = task.trigger.base_image_trigger
        if (commit_trigger_enabled or pull_request_trigger_enabled) or source_triggers:
            SourceTriggerUpdateParameters, SourceUpdateParameters, AuthInfoUpdateParameters = cmd.get_models(
                'SourceTriggerUpdateParameters', 'SourceUpdateParameters', 'AuthInfoUpdateParameters')

            source_trigger_events = _get_trigger_event_list(cmd,
                                                            source_triggers,
                                                            commit_trigger_enabled,
                                                            pull_request_trigger_enabled)
            source_trigger_update_params = [
                SourceTriggerUpdateParameters(
                    source_repository=SourceUpdateParameters(
                        source_control_type=source_control_type,
                        repository_url=context_path,
                        branch=branch,
                        source_control_auth_properties=AuthInfoUpdateParameters(
                            token=git_access_token,
                            token_type=DEFAULT_TOKEN_TYPE
                        )
                    ),
                    source_trigger_events=source_trigger_events,
                    status=TriggerStatus.enabled.value if source_trigger_events else TriggerStatus.disabled.value,
                    name=source_triggers[0].name if source_triggers else "defaultSourceTriggerName"
                )
            ]

        if base_image_trigger_enabled or base_image_trigger is not None:
            BaseImageTriggerUpdateParameters = cmd.get_models(
                'BaseImageTriggerUpdateParameters')

            status = None
            if base_image_trigger_enabled is not None:
                status = TriggerStatus.enabled.value if base_image_trigger_enabled else TriggerStatus.disabled.value
            base_image_trigger_update_params = BaseImageTriggerUpdateParameters(
                base_image_trigger_type=base_image_trigger_type,
                status=status,
                name=base_image_trigger.name if base_image_trigger else "defaultBaseimageTriggerName"
            )

    platform_os, platform_arch, platform_variant = None, None, None
    if platform:
        platform_os, platform_arch, platform_variant = get_validate_platform(cmd, platform)

    TaskUpdateParameters, PlatformUpdateParameters, AgentProperties, TriggerUpdateParameters = cmd.get_models(
        'TaskUpdateParameters', 'PlatformUpdateParameters', 'AgentProperties', 'TriggerUpdateParameters')
    taskUpdateParameters = TaskUpdateParameters(
        status=status,
        platform=PlatformUpdateParameters(
            os=platform_os,
            architecture=platform_arch,
            variant=platform_variant
        ),
        agent_configuration=AgentProperties(
            cpu=cpu
        ),
        timeout=timeout,
        step=step,
        trigger=TriggerUpdateParameters(
            source_triggers=source_trigger_update_params,
            base_image_trigger=base_image_trigger_update_params
        ),
        credentials=get_custom_registry_credentials(
            cmd=cmd,
            auth_mode=auth_mode
        )
    )

    return client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)


def acr_task_identity_assign(cmd,
                             client,
                             task_name,
                             registry_name,
                             identities=None,
                             resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    identity = _build_identities_info(cmd, identities)

    TaskUpdateParameters = cmd.get_models('TaskUpdateParameters')

    taskUpdateParameters = TaskUpdateParameters(
        identity=identity
    )

    return client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)


def acr_task_identity_remove(cmd,
                             client,
                             task_name,
                             registry_name,
                             identities=None,
                             resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    if identities and IDENTITY_GLOBAL_REMOVE in identities:
        if len(identities) > 1:
            raise CLIError(
                "Cannot specify additional identities when [all] is used in [--identities]")

    identity = None
    if not identities or IDENTITY_LOCAL_ID in identities:
        # To remove only the system assigned identity if user-assigned identities also exist
        # PATCH with the existing user-assigned identities
        # If no user-assigned identities exist, set the type to None
        existingIdentity = client.get_details(
            resource_group_name, registry_name, task_name).identity
        identities = IDENTITY_GLOBAL_REMOVE if not existingIdentity else list(
            existingIdentity.user_assigned_identities.keys())
        identity = _build_identities_info(cmd, identities)
    else:
        identity = _build_identities_info(cmd, identities, True)

    TaskUpdateParameters = cmd.get_models('TaskUpdateParameters')
    taskUpdateParameters = TaskUpdateParameters(
        identity=identity
    )

    return client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)


def acr_task_identity_show(cmd,
                           client,
                           task_name,
                           registry_name,
                           resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    identity = client.get_details(resource_group_name, registry_name, task_name).identity

    return {} if not identity else identity


def acr_task_credential_add(cmd,
                            client,
                            task_name,
                            registry_name,
                            login_server,
                            username=None,
                            password=None,
                            use_identity=None,
                            resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    existingCreds = client.get_details(resource_group_name, registry_name, task_name).credentials
    existingCreds = {} if not existingCreds else existingCreds.custom_registries

    if login_server in existingCreds:
        raise CLIError("Login server '{}' already exists. You cannot add it again.".format(login_server))

    TaskUpdateParameters = cmd.get_models('TaskUpdateParameters')
    taskUpdateParameters = TaskUpdateParameters(
        credentials=get_custom_registry_credentials(
            cmd=cmd,
            login_server=login_server,
            username=username,
            password=password,
            identity=use_identity
        )
    )

    resp = LongRunningOperation(cmd.cli_ctx)(
        client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)
    )
    resp = resp.credentials
    return {} if not resp else resp.custom_registries


def acr_task_credential_update(cmd,
                               client,
                               task_name,
                               registry_name,
                               login_server,
                               username=None,
                               password=None,
                               use_identity=None,
                               resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    existingCreds = client.get_details(resource_group_name, registry_name, task_name).credentials
    existingCreds = {} if not existingCreds else existingCreds.custom_registries

    if login_server not in existingCreds:
        raise CLIError("Login server '{}' not found.".format(login_server))

    TaskUpdateParameters = cmd.get_models('TaskUpdateParameters')
    taskUpdateParameters = TaskUpdateParameters(
        credentials=get_custom_registry_credentials(
            cmd=cmd,
            login_server=login_server,
            username=username,
            password=password,
            identity=use_identity
        )
    )

    resp = LongRunningOperation(cmd.cli_ctx)(
        client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)
    )
    resp = resp.credentials
    return {} if not resp else resp.custom_registries


def acr_task_credential_remove(cmd,
                               client,
                               task_name,
                               registry_name,
                               login_server,
                               resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    TaskUpdateParameters = cmd.get_models('TaskUpdateParameters')
    taskUpdateParameters = TaskUpdateParameters(
        credentials=get_custom_registry_credentials(
            cmd=cmd,
            login_server=login_server,
            is_remove=True
        )
    )

    resp = LongRunningOperation(cmd.cli_ctx)(
        client.update(resource_group_name, registry_name, task_name, taskUpdateParameters)
    )
    resp = resp.credentials
    return {} if not resp else resp.custom_registries


def acr_task_credential_list(cmd,
                             client,
                             task_name,
                             registry_name,
                             resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    resp = client.get_details(resource_group_name, registry_name, task_name).credentials
    return {} if not resp else resp.custom_registries


def acr_task_update_run(cmd,
                        client,
                        run_id,
                        registry_name,
                        no_archive=None,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    is_archive_enabled = not no_archive if no_archive is not None else None

    return client.update(resource_group_name=resource_group_name,
                         registry_name=registry_name,
                         run_id=run_id,
                         is_archive_enabled=is_archive_enabled)


def acr_task_run(cmd,
                 client,  # cf_acr_runs
                 task_name,
                 registry_name,
                 set_value=None,
                 set_secret=None,
                 no_logs=False,
                 no_wait=False,
                 resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    from ._client_factory import cf_acr_registries
    client_registries = cf_acr_registries(cmd.cli_ctx)
    TaskRunRequest = cmd.get_models('TaskRunRequest')

    queued_run = LongRunningOperation(cmd.cli_ctx)(
        client_registries.schedule_run(
            resource_group_name,
            registry_name,
            TaskRunRequest(
                task_name=task_name,
                values=(set_value if set_value else []) + (set_secret if set_secret else [])
            )
        )
    )

    run_id = queued_run.run_id
    logger.warning("Queued a run with ID: %s", run_id)

    if no_wait:
        return queued_run

    logger.warning("Waiting for an agent...")

    if no_logs:
        from ._run_polling import get_run_with_polling
        return get_run_with_polling(cmd, client, run_id, registry_name, resource_group_name)

    return stream_logs(client, run_id, registry_name, resource_group_name, True)


def acr_task_show_run(cmd,
                      client,  # cf_acr_runs
                      run_id,
                      registry_name,
                      resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, run_id)


def acr_task_cancel_run(cmd,
                        client,  # cf_acr_runs
                        run_id,
                        registry_name,
                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)
    return client.cancel(resource_group_name, registry_name, run_id)


def acr_task_list_runs(cmd,
                       client,  # cf_acr_runs
                       registry_name,
                       top=15,
                       task_name=None,
                       run_status=None,
                       image=None,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

    filter_str = None
    filter_str = _add_run_filter(filter_str, 'TaskName', task_name, 'eq')
    filter_str = _add_run_filter(filter_str, 'Status', run_status, 'eq')

    if image:
        from .repository import get_image_digest
        try:
            repository, _, manifest = get_image_digest(cmd, registry_name, image)
            filter_str = _add_run_filter(
                filter_str, 'OutputImageManifests', '{}@{}'.format(repository, manifest), 'contains')
        except CLIError as e:
            raise CLIError("Could not find image '{}'. {}".format(image, e))

    return client.list(resource_group_name, registry_name, filter=filter_str, top=top)


def _add_run_filter(orig_filter, name, value, operator):
    if not value:
        return orig_filter

    if operator == 'contains':
        new_filter_str = "contains({}, '{}')".format(name, value)
    elif operator == 'eq':
        new_filter_str = "{} eq '{}'".format(name, value)
    else:
        raise ValueError(
            "Allowed filter operator: {}".format(['contains', 'eq']))

    return "{} and {}".format(orig_filter, new_filter_str) if orig_filter else new_filter_str


def acr_task_logs(cmd,
                  client,  # cf_acr_runs
                  registry_name,
                  run_id=None,
                  task_name=None,
                  image=None,
                  resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, TASK_NOT_SUPPORTED)

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

    return stream_logs(client, run_id, registry_name, resource_group_name)


def _get_list_runs_message(base_message, task_name=None, image=None):
    if task_name:
        base_message = "{} for task '{}'".format(base_message, task_name)
    if image:
        base_message = "{} for image '{}'".format(base_message, image)
    return "{}.".format(base_message)


def _get_all_override_arguments(argument=None, secret_argument=None):
    arguments = None
    if argument is None and secret_argument is None:
        arguments = None
    else:
        arguments = (argument if argument else []) + (secret_argument if secret_argument else [])
    return arguments


def _build_identities_info(cmd, identities, is_remove=False):
    IdentityProperties, UserIdentityProperties, ResourceIdentityType = cmd.get_models(
        'IdentityProperties', 'UserIdentityProperties', 'ResourceIdentityType')
    identities = identities or []
    identity_types = []
    if IDENTITY_GLOBAL_REMOVE in identities:
        return IdentityProperties(type=ResourceIdentityType.none.value)
    if not identities or IDENTITY_LOCAL_ID in identities:
        identity_types.append(ResourceIdentityType.system_assigned.value)
    external_identities = [x for x in identities if x != IDENTITY_LOCAL_ID]
    if external_identities:
        identity_types.append(ResourceIdentityType.user_assigned.value)
    identity_types = ', '.join(identity_types)
    identity = IdentityProperties(type=identity_types)
    if external_identities:
        if is_remove:
            identity.user_assigned_identities = {e: None for e in external_identities}
        else:
            identity.user_assigned_identities = {e: UserIdentityProperties() for e in external_identities}
    return identity


def _get_trigger_event_list(cmd,
                            source_triggers,
                            commit_trigger_enabled=None,
                            pull_request_trigger_enabled=None):
    TriggerStatus, SourceTriggerEvent = cmd.get_models('TriggerStatus', 'SourceTriggerEvent')

    source_trigger_events = set()
    # perform merge with server-side event list
    if source_triggers:
        source_trigger_events = set(source_triggers[0].source_trigger_events)
        if source_triggers[0].status == TriggerStatus.disabled.value:
            source_trigger_events.clear()
    if commit_trigger_enabled is not None:
        if commit_trigger_enabled:
            source_trigger_events.add(SourceTriggerEvent.commit.value)
        else:
            if SourceTriggerEvent.commit.value in source_trigger_events:
                source_trigger_events.remove(SourceTriggerEvent.commit.value)
    if pull_request_trigger_enabled is not None:
        if pull_request_trigger_enabled:
            source_trigger_events.add(SourceTriggerEvent.pullrequest.value)
        else:
            if SourceTriggerEvent.pullrequest.value in source_trigger_events:
                source_trigger_events.remove(SourceTriggerEvent.pullrequest.value)
    return source_trigger_events
