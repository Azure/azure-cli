import os.path
import unittest
import mock

from azure.cli.command_modules.vm.custom import _load_images_from_aliases_doc

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
        images = _load_images_from_aliases_doc(None, None, None)

        #assert
        win_images = [i for i in images if i['publisher'] == 'MicrosoftWindowsServer']
        self.assertTrue(len(win_images) > 0)
        ubuntu_image = next(i for i in images if i['publisher'] == 'Canonical')
        self.assertEqual(ubuntu_image['publisher'], 'Canonical')
        self.assertEqual(ubuntu_image['offer'], 'UbuntuServer')

if __name__ == '__main__':
    unittest.main()
