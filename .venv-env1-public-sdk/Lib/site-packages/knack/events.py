# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

EVENT_CLI_PRE_EXECUTE = 'Cli.PreExecute'
EVENT_CLI_SUCCESSFUL_EXECUTE = 'Cli.SuccessfulExecute'
EVENT_CLI_POST_EXECUTE = 'Cli.PostExecute'

EVENT_INVOKER_PRE_CMD_TBL_CREATE = 'CommandInvoker.OnPreCommandTableCreate'
EVENT_INVOKER_POST_CMD_TBL_CREATE = 'CommandInvoker.OnPostCommandTableCreate'
EVENT_INVOKER_CMD_TBL_LOADED = 'CommandInvoker.OnCommandTableLoaded'
EVENT_INVOKER_PRE_PARSE_ARGS = 'CommandInvoker.OnPreParseArgs'
EVENT_INVOKER_POST_PARSE_ARGS = 'CommandInvoker.OnPostParseArgs'
EVENT_INVOKER_TRANSFORM_RESULT = 'CommandInvoker.OnTransformResult'
EVENT_INVOKER_FILTER_RESULT = 'CommandInvoker.OnFilterResult'

EVENT_PARSER_GLOBAL_CREATE = 'CommandParser.OnGlobalArgumentsCreate'

EVENT_CMDLOADER_LOAD_COMMAND_TABLE = 'CommandLoader.OnLoadCommandTable'
EVENT_CMDLOADER_LOAD_ARGUMENTS = 'CommandLoader.OnLoadArguments'

EVENT_COMMAND_CANCELLED = 'Command.OnOperationCancelled'
