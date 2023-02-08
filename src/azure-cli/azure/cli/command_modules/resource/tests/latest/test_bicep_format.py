
import unittest
from argparse import Namespace

class TestLoadArguments(unittest.TestCase):
    def test_load_arguments(self):
        # create mock object of self.argument_context
        self.argument_context = unittest.mock.MagicMock()
        self.argument_context.__enter__.return_value = self.argument_context

        # create mock object of bicep_file_type
        bicep_file_type = unittest.mock.MagicMock()

        # create mock object of bicep_outdir_type
        bicep_outdir_type = unittest.mock.MagicMock()

        # create mock object of bicep_outfile_type
        bicep_outfile_type = unittest.mock.MagicMock()

        # create mock object of bicep_stdout_type
        bicep_stdout_type = unittest.mock.MagicMock()

        # create mock object of bicep_indentkind_type
        bicep_indentkind_type = unittest.mock.MagicMock()

        # create mock object of bicep_indentsize_type
        bicep_indentsize_type = unittest.mock.MagicMock()

        # create mock object of bicep_insertfinalnewline_type
        bicep_insertfinalnewline_type = unittest.mock.MagicMock()

        # create mock object of bicep_newline_type
        bicep_newline_type = unittest.mock.MagicMock()

        # call load_arguments
        load_arguments(self, None)

        # assert that argument_context was called
        self.argument_context.assert_called_once_with('bicep format')

        # assert that argument was called with expected arguments
        self.argument_context.argument.assert_has_calls([
            unittest.mock.call('file', arg_type=bicep_file_type, help="The path to the Bicep file to format in the file system."),
            unittest.mock.call('outdir', arg_type=bicep_outdir_type),
            unittest.mock.call('outfile', arg_type=bicep_outfile_type),
            unittest.mock.call('stdout', arg_type=bicep_stdout_type),
            unittest.mock.call('indent_kind', arg_type=bicep_indentkind_type),
            unittest.mock.call('indent_size', arg_type=bicep_indentsize_type),
            unittest.mock.call('insert_final_newline', arg_type=bicep_insertfinalnewline_type),
            unittest.mock.call('newline', arg_type=bicep_newline_type),
        ])
