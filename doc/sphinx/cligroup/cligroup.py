# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import copy
from docutils import nodes
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util.compat import Directive
from sphinx.util.docfields import Field

cli_field_types = [
        Field('summary', label='Summary', has_arg=False,
                   names=('summary', 'shortdesc')),
        Field('description', label='Description', has_arg=False,
                   names=('description', 'desc', 'longdesc'))
    ]

class CliBaseDirective(ObjectDescription):
    def handle_signature(self, sig, signode):
        signode += addnodes.desc_addname(sig, sig)
        return sig

    def needs_arglist(self):
        return False

    def add_target_and_index(self, name, sig, signode):
        signode['ids'].append(name)

    def get_index_text(self, modname, name):
        return name

class CliGroupDirective(CliBaseDirective):
    doc_field_types = copy.copy(cli_field_types)
    doc_field_types.append(
        Field('docsource', label='Doc Source', has_arg=False,
                   names=('docsource', 'documentsource'))
    )

class CliCommandDirective(CliBaseDirective):
    doc_field_types = copy.copy(cli_field_types)
    doc_field_types.append(
        Field('docsource', label='Doc Source', has_arg=False,
                   names=('docsource', 'documentsource'))
    )

class CliArgumentDirective(CliBaseDirective):
    doc_field_types = copy.copy(cli_field_types)
    doc_field_types.extend([
        Field('required', label='Required', has_arg=False,
            names=('required')),
        Field('values', label='Allowed values', has_arg=False,
            names=('values', 'choices', 'options')),
        Field('default', label='Default value', has_arg=False,
            names=('default')),
        Field('source', label='Values from', has_arg=False,
            names=('source', 'sources'))
     ])

class CliExampleDirective(CliBaseDirective):
    pass

def setup(app):
    app.add_directive('cligroup', CliGroupDirective)
    app.add_directive('clicommand', CliCommandDirective)
    app.add_directive('cliarg', CliArgumentDirective)
    app.add_directive('cliexample', CliExampleDirective)
