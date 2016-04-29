import os.path
import unittest
import mock

from azure.cli.command_modules.vm.custom import read_images_from_aliases_doc

class TestVMImage(unittest.TestCase):
    @mock.patch('azure.cli.command_modules.vm.custom.urlopen', autospec=True)
    def test_read_images_from_alias_doc(self, mock_urlopen):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'aliases.json')
        with open(file_path, 'r') as test_file:
            test_data = test_file.read().encode()

        mock_read = mock.MagicMock()
        mock_read.read.return_value = test_data
        mock_urlopen.return_value = mock_read

        #action
        images = read_images_from_aliases_doc()

        #assert
        self.assertEqual(images['Windows']['Win2012Datacenter']['publisher'],
                         'MicrosoftWindowsServer')
        self.assertEqual(images['Linux']['UbuntuLTS']['publisher'], 'Canonical')
        self.assertEqual(images['Linux']['UbuntuLTS']['urn'],
                         'Canonical:UbuntuServer:14.04.4-LTS:latest')

if __name__ == '__main__':
    unittest.main()
