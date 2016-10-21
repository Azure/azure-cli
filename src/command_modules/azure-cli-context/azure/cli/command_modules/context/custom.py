#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import azure.cli.core.context as ctx
from azure.cli.core._util import CLIError
from azure.cli.core.cloud import CloudNotRegisteredException

def list_contexts():
    return ctx.get_contexts()

def activate_context(context_name):
    try:
        ctx.set_active_context(context_name)
    except ctx.ContextNotFoundException as e:
        raise CLIError(e)

def delete_context(context_name):
    try:
        ctx.delete_context(context_name)
    except ctx.ContextNotFoundException as e:
        raise CLIError(e)
    except ctx.CannotDeleteDefaultContextException as e:
        raise CLIError(e)
    except ctx.CannotDeleteActiveContextException as e:
        raise CLIError(e)

def create_context(context_name, cloud_name, use_later=False):
    try:
        ctx.create_context(context_name, cloud_name)
    except ctx.ContextExistsException as e:
        raise CLIError(e)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
    if not use_later:
        ctx.set_active_context(context_name)

def show_contexts(context_name=None):
    if not context_name:
        context_name = ctx.get_active_context_name()
    try:
        return ctx.get_context(context_name)
    except ctx.ContextNotFoundException as e:
        raise CLIError(e)

def modify_context(context_name=None, cloud_name=None, default_subscription=None):
    if not context_name:
        context_name = ctx.get_active_context_name()
    try:
        ctx.modify_context(context_name,
                           cloud_name=cloud_name,
                           default_subscription=default_subscription)
    except ctx.ContextExistsException as e:
        raise CLIError(e)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
