#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
from six.moves import configparser

from azure.cli.core._config import (CONTEXT_CONFIG_DIR, GLOBAL_CONFIG_DIR)

class ContextNotFoundException(Exception):
    def __init__(self, context_name):
        super(ContextNotFoundException, self).__init__(context_name)
        self.context_name = context_name
    def __str__(self):
        return "The context '{}' does not exist.".format(self.context_name)

class ContextExistsException(Exception):
    def __init__(self, context_name):
        super(ContextExistsException, self).__init__(context_name)
        self.context_name = context_name
    def __str__(self):
        return "The context '{}' already exists.".format(self.context_name)

class CannotDeleteActiveContextException(Exception):
    def __str__(self):
        return "You cannot delete the current active context"

class CannotDeleteDefaultContextException(Exception):
    def __str__(self):
        return "You cannot delete the default context."

ACTIVE_CONTEXT_FILE = os.path.join(GLOBAL_CONFIG_DIR, 'active_context')
ACTIVE_CONTEXT_ENV_VAR = os.environ.get('AZURE_CONTEXT', None)
DEFAULT_CONTEXT_NAME = 'default'

get_active_context = lambda: get_context(get_active_context_name())
context_exists = lambda n: any([x for x in get_context_names() if x == n])
get_context_file_path = lambda n: os.path.join(CONTEXT_CONFIG_DIR, n)
get_contexts = lambda: [get_context(context_name) for context_name in get_context_names()]

def _set_active_subscription(context):
    ''' Set the active subscription used by Profile '''
    from azure.cli.core._profile import Profile, _ENVIRONMENT_NAME, _SUBSCRIPTION_ID, _STATE
    profile = Profile()
    subscriptions = profile.load_cached_subscriptions()
    context_file_path = get_context_file_path(context['name'])
    context_config = configparser.SafeConfigParser()
    context_config.read(context_file_path)
    subscription_to_use = None
    try:
        subscription_to_use = context_config.get('context', 'default_subscription')
    except (configparser.NoSectionError, configparser.NoOptionError):
        # Fallback to finding the first subscription that is for this cloud
        for sub in subscriptions:
            if sub[_ENVIRONMENT_NAME] == context['cloud'] and sub[_STATE] == 'Enabled':
                subscription_to_use = sub[_SUBSCRIPTION_ID]
                break
    if subscription_to_use:
        profile.set_active_subscription(subscription_to_use)

def get_active_context_name():
    if ACTIVE_CONTEXT_ENV_VAR:
        return ACTIVE_CONTEXT_ENV_VAR
    try:
        with open(ACTIVE_CONTEXT_FILE, "r") as active_context_file:
            return active_context_file.read()
    except (OSError, IOError):
        return DEFAULT_CONTEXT_NAME

def set_active_context(context_name, skip_set_active_subsciption=False):
    if not context_exists(context_name):
        raise ContextNotFoundException(context_name)
    with open(ACTIVE_CONTEXT_FILE, "w") as active_context_file:
        active_context_file.write(context_name)
    if not skip_set_active_subsciption:
        _set_active_subscription(get_active_context())

def get_context_names():
    if os.path.isdir(CONTEXT_CONFIG_DIR):
        contexts = [f for f in os.listdir(CONTEXT_CONFIG_DIR) \
               if os.path.isfile(os.path.join(CONTEXT_CONFIG_DIR, f))]
        if contexts:
            return contexts
    # No contexts yet. Let's create the default one now.
    # We want to skip the exists check because checking if exists
    # involves getting the context names (which is this function)
    from azure.cli.core.cloud import AZURE_PUBLIC_CLOUD
    create_context(DEFAULT_CONTEXT_NAME, AZURE_PUBLIC_CLOUD.name, skip_exists_check=True)
    set_active_context(DEFAULT_CONTEXT_NAME, skip_set_active_subsciption=True)
    return [DEFAULT_CONTEXT_NAME]

def get_context(context_name):
    if not context_exists(context_name):
        raise ContextNotFoundException(context_name)
    context_config = configparser.SafeConfigParser()
    context_config.read(get_context_file_path(context_name))
    context = {'name': context_name, 'active': context_name == get_active_context_name()}
    context_section_name = 'context'
    try:
        for option in context_config.options(context_section_name):
            try:
                context[option] = context_config.get(context_section_name, option)
            except (configparser.NoSectionError, configparser.NoOptionError):
                context[option] = None
    except configparser.NoSectionError:
        pass
    return context

def delete_context(context_name):
    if not context_exists(context_name):
        raise ContextNotFoundException(context_name)
    if context_name == DEFAULT_CONTEXT_NAME:
        raise CannotDeleteDefaultContextException()
    if context_name == get_active_context_name():
        raise CannotDeleteActiveContextException()
    os.remove(get_context_file_path(context_name))

def create_context(context_name, cloud_name, skip_exists_check=False):
    from azure.cli.core.cloud import get_cloud
    if not skip_exists_check and context_exists(context_name):
        raise ContextExistsException(context_name)
    cloud = get_cloud(cloud_name)
    context_file_path = get_context_file_path(context_name)
    context_config = configparser.SafeConfigParser()
    context_config.read(context_file_path)
    try:
        context_config.add_section('context')
    except configparser.DuplicateSectionError:
        pass
    context_config.set('context', 'cloud', cloud.name)
    if not os.path.isdir(CONTEXT_CONFIG_DIR):
        os.makedirs(CONTEXT_CONFIG_DIR)
    with open(context_file_path, 'w') as configfile:
        context_config.write(configfile)

def modify_context(context_name, cloud_name=None, default_subscription=None):
    from azure.cli.core.cloud import get_cloud
    if not context_exists(context_name):
        raise ContextNotFoundException(context_name)
    if cloud_name or default_subscription:
        context_file_path = get_context_file_path(context_name)
        context_config = configparser.SafeConfigParser()
        context_config.read(context_file_path)
        if cloud_name:
            cloud = get_cloud(cloud_name)
            context_config.set('context', 'cloud', cloud.name)
        if default_subscription is not None:
            if default_subscription:
                context_config.set('context', 'default_subscription', default_subscription)
            else:
                context_config.remove_option('context', 'default_subscription')
        with open(context_file_path, 'w') as configfile:
            context_config.write(configfile)
        active_context = get_active_context()
        if context_name == active_context['name']:
            # User has changed the cloud or default subscription for the current context
            # so update the active subscription we use
            _set_active_subscription(active_context)
