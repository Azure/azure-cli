# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('postgres flexible-server create', '--high-availability', redirect='--zonal-resiliency')
register_argument_deprecate('postgres flexible-server update', '--high-availability', redirect='--zonal-resiliency')
