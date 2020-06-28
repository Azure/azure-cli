#!/usr/bin/env python

# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
An interface to be run from the command line/powershell.

This file is the only executable in the project.
"""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import cmd
from datetime import datetime
import os
import stat
import sys

from azure.datalake.store.core import AzureDLFileSystem
from azure.datalake.store.multithread import ADLDownloader, ADLUploader
from azure.datalake.store.utils import write_stdout


class AzureDataLakeFSCommand(cmd.Cmd, object):
    """Accept commands via an interactive prompt or the command line."""

    prompt = 'azure> '
    undoc_header = None
    _hidden_methods = ('do_EOF',)

    def __init__(self, fs):
        super(AzureDataLakeFSCommand, self).__init__()
        self._fs = fs

    def get_names(self):
        return [n for n in dir(self.__class__) if n not in self._hidden_methods]

    def do_close(self, line):
        return True

    def help_close(self):
        print("close\n")
        print("Exit the application")

    def do_cat(self, line):
        parser = argparse.ArgumentParser(prog="cat", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for f in args.files:
            write_stdout(self._fs.cat(f))

    def help_cat(self):
        print("cat file ...\n")
        print("Display contents of files")

    def do_chgrp(self, line):
        parser = argparse.ArgumentParser(prog="chgrp", add_help=False)
        parser.add_argument('group', type=str)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for f in args.files:
            self._fs.chown(f, group=args.group)

    def help_chgrp(self):
        print("chgrp group file ...\n")
        print("Change file group")

    def do_chmod(self, line):
        parser = argparse.ArgumentParser(prog="chmod", add_help=False)
        parser.add_argument('mode', type=str)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for f in args.files:
            self._fs.chmod(f, args.mode)

    def help_chmod(self):
        print("chmod mode file ...\n")
        print("Change file permissions")

    def _parse_ownership(self, ownership):
        if ':' in ownership:
            owner, group = ownership.split(':')
            if not owner:
                owner = None
        else:
            owner = ownership
            group = None
        return owner, group

    def do_chown(self, line):
        parser = argparse.ArgumentParser(prog="chown", add_help=False)
        parser.add_argument('ownership', type=str)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        owner, group = self._parse_ownership(args.ownership)

        for f in args.files:
            self._fs.chown(f, owner=owner, group=group)

    def help_chown(self):
        print("chown owner[:group] file ...")
        print("chown :group file ...\n")
        print("Change file owner and group")

    def _display_dict(self, d):
        width = max([len(k) for k in d.keys()])
        for k, v in sorted(list(d.items())):
            print("{0:{width}} = {1}".format(k, v, width=width))

    def do_df(self, line):
        parser = argparse.ArgumentParser(prog="df", add_help=False)
        parser.add_argument('path', type=str, nargs='?', default='.')
        args = parser.parse_args(line.split())

        self._display_dict(self._fs.df(args.path))

    def help_df(self):
        print("df [path]\n")
        print("Display Azure account statistics of a path")

    def _truncate(self, num, fmt):
        return '{:{fmt}}'.format(num, fmt=fmt).rstrip('0').rstrip('.')

    def _format_size(self, num):
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if abs(num) < 1024.0:
                return '{:>4s}{}'.format(self._truncate(num, '3.1f'), unit)
            num /= 1024.0
        return self._truncate(num, '.1f') + 'P'

    def _display_path_with_size(self, name, size, human_readable):
        if human_readable:
            print("{:7s} {}".format(self._format_size(size), name))
        else:
            print("{:<9d} {}".format(size, name))

    def do_du(self, line):
        parser = argparse.ArgumentParser(prog="du", add_help=False)
        parser.add_argument('files', type=str, nargs='*', default=[''])
        parser.add_argument('-c', '--total', action='store_true')
        parser.add_argument('-h', '--human-readable', action='store_true')
        parser.add_argument('-r', '--recursive', action='store_true')
        args = parser.parse_args(line.split())

        total = 0
        for f in args.files:
            items = sorted(list(self._fs.du(f, deep=args.recursive).items()))
            for name, size in items:
                total += size
                self._display_path_with_size(name, size, args.human_readable)
        if args.total:
            self._display_path_with_size("total", total, args.human_readable)

    def help_du(self):
        print("du [-c | --total] [-r | --recursive] [-h | --human-readable] [file ...]\n")
        print("Display disk usage statistics")

    def do_exists(self, line):
        parser = argparse.ArgumentParser(prog="exists", add_help=False)
        parser.add_argument('file', type=str)
        args = parser.parse_args(line.split())

        print(self._fs.exists(args.file, invalidate_cache=False))

    def help_exists(self):
        print("exists file\n")
        print("Check if file/directory exists")

    def do_get(self, line):
        parser = argparse.ArgumentParser(prog="get", add_help=False)
        parser.add_argument('remote_path', type=str)
        parser.add_argument('local_path', type=str, nargs='?', default='.')
        parser.add_argument('-b', '--chunksize', type=int, default=2**28)
        parser.add_argument('-c', '--threads', type=int, default=None)
        parser.add_argument('-f', '--force', action='store_true')
        args = parser.parse_args(line.split())

        ADLDownloader(self._fs, args.remote_path, args.local_path,
                      nthreads=args.threads, chunksize=args.chunksize,
                      overwrite=args.force)

    def help_get(self):
        print("get [option]... remote-path [local-path]\n")
        print("Retrieve the remote path and store it locally\n")
        print("Options:")
        print("    -b <int>")
        print("    --chunksize <int>")
        print("        Set size of chunk to retrieve atomically, in bytes.\n")
        print("    -c <int>")
        print("    --threads <int>")
        print("        Set number of multiple requests to perform at a time.")
        print("    -f")
        print("    --force")
        print("        Overwrite an existing file or directory.")

    def do_head(self, line):
        parser = argparse.ArgumentParser(prog="head", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        parser.add_argument('-c', '--bytes', type=int, default=1024)
        args = parser.parse_args(line.split())

        for f in args.files:
            write_stdout(self._fs.head(f, size=args.bytes))

    def help_head(self):
        print("head [-c bytes | --bytes bytes] file ...\n")
        print("Display first bytes of a file")

    def do_info(self, line):
        parser = argparse.ArgumentParser(prog="info", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for f in args.files:
            self._display_dict(self._fs.info(f, invalidate_cache=False))

    def help_info(self):
        print("info file ...\n")
        print("Display file information")

    def _display_item(self, item, human_readable):
        mode = int(item['permission'], 8)

        if item['type'] == 'DIRECTORY':
            permissions = "d"
        elif item['type'] == 'SYMLINK':
            permissions = "l"
        else:
            permissions = "-"

        permissions += "r" if bool(mode & stat.S_IRUSR) else "-"
        permissions += "w" if bool(mode & stat.S_IWUSR) else "-"
        permissions += "x" if bool(mode & stat.S_IXUSR) else "-"
        permissions += "r" if bool(mode & stat.S_IRGRP) else "-"
        permissions += "w" if bool(mode & stat.S_IWGRP) else "-"
        permissions += "x" if bool(mode & stat.S_IXGRP) else "-"
        permissions += "r" if bool(mode & stat.S_IROTH) else "-"
        permissions += "w" if bool(mode & stat.S_IWOTH) else "-"
        permissions += "x" if bool(mode & stat.S_IXOTH) else "-"

        timestamp = item['modificationTime'] // 1000
        modified_at = datetime.fromtimestamp(timestamp).strftime('%b %d %H:%M')

        if human_readable:
            size = "{:5s}".format(self._format_size(item['length']))
        else:
            size = "{:9d}".format(item['length'])

        print("{} {} {} {} {} {}".format(
            permissions,
            item['owner'][:8],
            item['group'][:8],
            size,
            modified_at,
            os.path.basename(item['name'])))

    def do_ls(self, line):
        parser = argparse.ArgumentParser(prog="ls", add_help=False)
        parser.add_argument('dirs', type=str, nargs='*', default=[''])
        parser.add_argument('-h', '--human-readable', action='store_true')
        parser.add_argument('-l', '--detail', action='store_true')
        args = parser.parse_args(line.split())

        for d in args.dirs:
            for item in self._fs.ls(d, detail=args.detail, invalidate_cache=False):
                if args.detail:
                    self._display_item(item, args.human_readable)
                else:
                    print(os.path.basename(item))

    def help_ls(self):
        print("ls [-h | --human-readable] [-l | --detail] [file ...]\n")
        print("List directory contents")

    def do_mkdir(self, line):
        parser = argparse.ArgumentParser(prog="mkdir", add_help=False)
        parser.add_argument('dirs', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for d in args.dirs:
            self._fs.mkdir(d)

    def help_mkdir(self):
        print("mkdir directory ...\n")
        print("Create directories")

    def do_mv(self, line):
        parser = argparse.ArgumentParser(prog="mv", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        self._fs.mv(args.files[0], args.files[1])

    def help_mv(self):
        print("mv from-path to-path\n")
        print("Rename from-path to to-path")

    def do_put(self, line):
        parser = argparse.ArgumentParser(prog="put", add_help=False)
        parser.add_argument('local_path', type=str)
        parser.add_argument('remote_path', type=str, nargs='?', default='.')
        parser.add_argument('-b', '--chunksize', type=int, default=2**28)
        parser.add_argument('-c', '--threads', type=int, default=None)
        parser.add_argument('-f', '--force', action='store_true')
        args = parser.parse_args(line.split())

        ADLUploader(self._fs, args.remote_path, args.local_path,
                    nthreads=args.threads, chunksize=args.chunksize,
                    overwrite=args.force)

    def help_put(self):
        print("put [option]... local-path [remote-path]\n")
        print("Store a local file on the remote machine\n")
        print("Options:")
        print("    -b <int>")
        print("    --chunksize <int>")
        print("        Set size of chunk to store atomically, in bytes.\n")
        print("    -c <int>")
        print("    --threads <int>")
        print("        Set number of multiple requests to perform at a time.")
        print("    -f")
        print("    --force")
        print("        Overwrite an existing file or directory.")

    def do_quit(self, line):
        return True

    def help_quit(self):
        print("quit\n")
        print("Exit the application")

    def do_rm(self, line):
        parser = argparse.ArgumentParser(prog="rm", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        parser.add_argument('-r', '--recursive', action='store_true')
        args = parser.parse_args(line.split())

        for f in args.files:
            self._fs.rm(f, recursive=args.recursive)

    def help_rm(self):
        print("rm [-r | --recursive] file ...\n")
        print("Remove directory entries")

    def do_rmdir(self, line):
        parser = argparse.ArgumentParser(prog="rmdir", add_help=False)
        parser.add_argument('dirs', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for d in args.dirs:
            self._fs.rmdir(d)

    def help_rmdir(self):
        print("rmdir directory ...\n")
        print("Remove directories")

    def do_tail(self, line):
        parser = argparse.ArgumentParser(prog="tail", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        parser.add_argument('-c', '--bytes', type=int, default=1024)
        args = parser.parse_args(line.split())

        for f in args.files:
            write_stdout(self._fs.tail(f, size=args.bytes))

    def help_tail(self):
        print("tail [-c bytes | --bytes bytes] file ...\n")
        print("Display last bytes of a file")

    def do_touch(self, line):
        parser = argparse.ArgumentParser(prog="touch", add_help=False)
        parser.add_argument('files', type=str, nargs='+')
        args = parser.parse_args(line.split())

        for f in args.files:
            self._fs.touch(f)

    def help_touch(self):
        print("touch file ...\n")
        print("Change file access and modification times")

    def do_EOF(self, line):
        return True

    def do_list_uploads(self, line):
        print(ADLUploader.load())

    def help_list_uploads(self):
        print("Shows interrupted but persisted downloads")

    def do_clear_uploads(self, line):
        ADLUploader.clear_saved()

    def help_clear_uploads(self):
        print("Forget all persisted uploads")

    def do_resume_upload(self, line):
        try:
            up = ADLUploader.load()[line]
            up.run()
        except KeyError:
            print("No such upload")

    def help_resume_upload(self):
        print("resume_upload name")
        print()
        print("Restart the upload designated by <name> and run until done.")

    def do_list_downloads(self, line):
        print(ADLDownloader.load())

    def help_list_downloads(self):
        print("Shows interrupted but persisted uploads")

    def do_clear_downloads(self, line):
        ADLDownloader.clear_saved()

    def help_clear_downloads(self):
        print("Forget all persisted downloads")

    def do_resume_download(self, line):
        try:
            up = ADLDownloader.load()[line]
            up.run()
        except KeyError:
            print("No such download")

    def help_resume_download(self):
        print("resume_download name")
        print()
        print("Restart the download designated by <name> and run until done.")


def setup_logging(default_level='WARNING'):
    """ Setup logging configuration

    The logging configuration can be overridden with one environment variable:

    ADLFS_LOG_LEVEL (defines logging level)
    """
    import logging
    import os
    import sys

    log_level = os.environ.get('ADLFS_LOG_LEVEL', default_level)

    levels = dict(
        CRITICAL=logging.CRITICAL,
        ERROR=logging.ERROR,
        WARNING=logging.WARNING,
        INFO=logging.INFO,
        DEBUG=logging.DEBUG)

    if log_level in levels:
        log_level = levels[log_level]
    else:
        sys.exit("invalid ADLFS_LOG_LEVEL '{0}'".format(log_level))

    logging.basicConfig(level=log_level)


if __name__ == '__main__':
    setup_logging()
    fs = AzureDLFileSystem()
    if len(sys.argv) > 1:
        AzureDataLakeFSCommand(fs).onecmd(' '.join(sys.argv[1:]))
    else:
        AzureDataLakeFSCommand(fs).cmdloop()
