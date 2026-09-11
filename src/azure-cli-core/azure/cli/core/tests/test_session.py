# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import json
import os
import shutil
import stat
import tempfile
import unittest
from unittest import mock

from azure.cli.core._session import Session


class TestSession(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.filename = os.path.join(self.dir, 'test.json')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _session(self, data):
        session = Session()
        session.filename = self.filename
        session.data = data
        return session

    def _read(self):
        with open(self.filename, encoding='utf-8-sig') as f:
            return json.load(f)

    def _temp_files(self):
        return [name for name in os.listdir(self.dir) if name.endswith('.tmp')]

    def test_save_writes_the_data(self):
        self._session({'a': 1}).save()
        self.assertEqual(self._read(), {'a': 1})

    def test_save_replaces_the_file_instead_of_truncating_it(self):
        # A truncating write leaves the file empty or half written while it runs, and a concurrent
        # reader that fails to parse it has load() overwrite it with defaults. Replacing the file
        # means a reader always sees either the old contents or the new ones.
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            json.dump({'a': 1}, f)
        inode = os.stat(self.filename).st_ino

        self._session({'a': 2}).save()

        self.assertNotEqual(os.stat(self.filename).st_ino, inode)
        self.assertEqual(self._read(), {'a': 2})

    def test_save_leaves_the_file_intact_when_the_data_cannot_be_serialized(self):
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            json.dump({'kept': True}, f)

        with self.assertRaises(TypeError):
            self._session({'a': 'fine', 'b': {1, 2}}).save()

        self.assertEqual(self._read(), {'kept': True})
        self.assertFalse(self._temp_files())

    @unittest.skipIf(os.name == 'nt', 'POSIX file permissions not applicable on Windows')
    def test_save_preserves_the_permissions_of_an_existing_file(self):
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            json.dump({}, f)
        os.chmod(self.filename, 0o644)

        self._session({'a': 1}).save()

        self.assertEqual(stat.S_IMODE(os.stat(self.filename).st_mode), 0o644)

    @unittest.skipIf(os.name == 'nt', 'Symlink test not applicable on Windows')
    def test_save_follows_a_symlink_rather_than_replacing_it(self):
        target = os.path.join(self.dir, 'target.json')
        link = os.path.join(self.dir, 'link.json')
        with open(target, 'w', encoding='utf-8-sig') as f:
            json.dump({'a': 1}, f)
        os.symlink(target, link)

        session = Session()
        session.filename = link
        session.data = {'a': 2}
        session.save()

        self.assertTrue(os.path.islink(link))
        with open(target, encoding='utf-8-sig') as f:
            self.assertEqual(json.load(f), {'a': 2})

    @unittest.skipIf(os.name == 'nt', 'directory permissions are not enforced the same way on Windows')
    def test_save_still_writes_when_the_directory_is_not_writable(self):
        # Locked down containers and build images mount the config directory read only while
        # leaving the file itself writable. A save that used to succeed there must keep working.
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            json.dump({}, f)
        os.chmod(self.dir, 0o500)
        try:
            self._session({'a': 1}).save()
            self.assertEqual(self._read(), {'a': 1})
        finally:
            os.chmod(self.dir, 0o700)

    def test_save_does_not_fall_back_when_the_temporary_file_fails_for_another_reason(self):
        # The in place write would also fail on a full disk, and it would lose the file doing it,
        # so only a permission problem should reach the fallback.
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            json.dump({'kept': True}, f)

        with mock.patch('tempfile.mkstemp', side_effect=OSError(errno.ENOSPC, 'No space left')):
            with self.assertRaises(OSError):
                self._session({'a': 1}).save()

        self.assertEqual(self._read(), {'kept': True})

    def test_load_reads_back_what_save_wrote(self):
        self._session({'a': 1}).save()

        session = Session()
        session.load(self.filename)

        self.assertEqual(session.data, {'a': 1})

    def test_load_overrides_a_file_that_cannot_be_parsed(self):
        with open(self.filename, 'w', encoding='utf-8-sig') as f:
            f.write('{"truncated"')

        session = Session()
        session.load(self.filename)

        self.assertEqual(session.data, {})
        self.assertEqual(self._read(), {})


if __name__ == '__main__':
    unittest.main()
