import uuid
import re

from azure.cli._util import CLIError
from azure.mgmt.authorization.models import RoleAssignmentProperties
from ._params import _auth_client_factory

#TODO: expand the support to be in parity with node cli
def create_role_assignment(role, object_id, scope=None):
    assignments_client = _auth_client_factory().role_assignments
    definitions_client = _auth_client_factory().role_definitions
    role_id = role
    scope = scope or '/subscriptions/' + definitions_client.config.subscription_id
    if not re.match(r'[0-9a-f]{32}\Z', role, re.I): #retrieve role id
        role_defs = list(definitions_client.list(scope, "roleName eq '{}'".format(role)))
        if not role_defs:
            raise CLIError('Role {} doesn\'t exist.'.format(role))
        elif len(role_defs) > 1:
            raise CLIError('More than one roles match the given name {}'.format(role))
        role_id = role_defs[0].id

    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    return assignments_client.create(scope, assignment_name, properties)

