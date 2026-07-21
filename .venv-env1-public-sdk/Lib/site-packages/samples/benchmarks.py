from __future__ import print_function

import functools
import hashlib
import logging
import os
import shutil
import sys
import time

from azure.datalake.store import core, multithread
from azure.datalake.store.transfer import ADLTransferClient
from azure.datalake.store.utils import WIN
from tests.testing import md5sum


def benchmark(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        print('[%s] starting...' % (f.__name__))
        start = time.time()
        result = f(*args, **kwargs)
        stop = time.time()
        elapsed = stop - start
        print('[%s] finished in %2.4fs' % (f.__name__, elapsed))
        return result, elapsed

    return wrapped


def mock_client(adl, nthreads):
    def transfer(adlfs, src, dst, offset, size, buffersize, blocksize, shutdown_event=None):
        pass

    def merge(adlfs, outfile, files, shutdown_event=None):
        pass

    return ADLTransferClient(
        adl,
        'foo',
        transfer=transfer,
        merge=merge,
        nthreads=nthreads)


def checksum(path):
    """ Generate checksum for file/directory content """
    if not os.path.exists(path):
        return None
    if os.path.isfile(path):
        return md5sum(path)
    partial_sums = []
    for root, dirs, files in os.walk(path):
        for f in files:
            filename = os.path.join(root, f)
            if os.path.exists(filename):
                partial_sums.append(str.encode(md5sum(filename)))
    return hashlib.md5(b''.join(sorted(partial_sums))).hexdigest()


def du(path):
    """ Find total size of content used by path """
    if os.path.isfile(path):
        return os.path.getsize(path)
    size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            size += os.path.getsize(os.path.join(root, f))
    return size


def verify(instance):
    """ Confirm whether target file matches source file """
    adl = instance.client._adlfs
    lfile = instance.lpath
    rfile = instance.rpath

    print("finish w/o error:", instance.successful())
    print("local file      :", lfile)
    if os.path.exists(lfile):
        print("local file size :", du(lfile))
    else:
        print("local file size :", None)

    print("remote file     :", rfile)
    if adl.exists(rfile, invalidate_cache=False):
        print("remote file size:", adl.du(rfile, total=True, deep=True))
    else:
        print("remote file size:", None)


@benchmark
def bench_upload_1_50gb(adl, lpath, rpath, config):
    return multithread.ADLUploader(
        adl,
        lpath=lpath,
        rpath=rpath,
        **config[bench_upload_1_50gb.__name__])


@benchmark
def bench_upload_50_1gb(adl, lpath, rpath, config):
    return multithread.ADLUploader(
        adl,
        lpath=lpath,
        rpath=rpath,
        **config[bench_upload_50_1gb.__name__])


@benchmark
def bench_download_1_50gb(adl, lpath, rpath, config):
    return multithread.ADLDownloader(
        adl,
        lpath=lpath,
        rpath=rpath,
        **config[bench_download_1_50gb.__name__])


@benchmark
def bench_download_50_1gb(adl, lpath, rpath, config):
    return multithread.ADLDownloader(
        adl,
        lpath=lpath,
        rpath=rpath,
        **config[bench_download_50_1gb.__name__])


def setup_logging(level='INFO'):
    """ Log only Azure messages, ignoring 3rd-party libraries """
    levels = dict(
        CRITICAL=logging.CRITICAL,
        ERROR=logging.ERROR,
        WARNING=logging.WARNING,
        INFO=logging.INFO,
        DEBUG=logging.DEBUG)

    if level in levels:
        level = levels[level]
    else:
        raise ValueError('invalid log level: {}'.format(level))

    logging.basicConfig(
        format='%(asctime)s %(name)-17s %(levelname)-8s %(message)s')
    logger = logging.getLogger('azure.datalake.store')
    logger.setLevel(level)


def print_summary_statistics(stats):
    from statistics import mean, median, pstdev

    print("benchmark min mean sd median max")
    for benchmark, samples in stats.items():
        if samples:
            metrics = [int(round(fn(samples), 0)) for fn in [min, mean, pstdev, median, max]]
        else:
            metrics = [0, 0, 0, 0, 0]
        print(benchmark, *metrics)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('local_path', type=str)
    parser.add_argument('remote_path', type=str)
    parser.add_argument('-l', '--log-level', default='INFO')
    parser.add_argument('-n', '--iterations', default=1, type=int)
    parser.add_argument('-q', '--quiet', dest='verbose', action='store_false')
    parser.add_argument('-s', '--statistics', action='store_true')
    parser.add_argument('--no-verify', dest='verify', action='store_false')
    parser.add_argument('--no-checksum', dest='validate', action='store_false')

    args = parser.parse_args(sys.argv[1:])

    setup_logging(level=args.log_level)

    adl = core.AzureDLFileSystem()

    # Required setup until outstanding issues are resolved
    adl.mkdir(args.remote_path)

    # OS-specific settings

    if WIN:
        config = {
            'bench_upload_1_50gb': {
                'nthreads': 64,
                'buffersize': 32 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_upload_50_1gb': {
                'nthreads': 64,
                'buffersize': 32 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_download_1_50gb': {
                'nthreads': 64,
                'buffersize': 32 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_download_50_1gb': {
                'nthreads': 64,
                'buffersize': 32 * 2**20,
                'blocksize': 4 * 2**20
            }
        }
    else:
        config = {
            'bench_upload_1_50gb': {
                'nthreads': 64,
                'buffersize': 4 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_upload_50_1gb': {
                'nthreads': 64,
                'buffersize': 4 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_download_1_50gb': {
                'nthreads': 16,
                'buffersize': 4 * 2**20,
                'blocksize': 4 * 2**20
            },
            'bench_download_50_1gb': {
                'nthreads': 16,
                'buffersize': 4 * 2**20,
                'blocksize': 4 * 2**20
            }
        }

    for benchmark in config:
        config[benchmark]['verbose'] = args.verbose

    stats = {}

    for _ in range(args.iterations):
        # Upload/download 1 50GB files

        lpath_up = os.path.join(args.local_path, '50gbfile.txt')
        lpath_down = os.path.join(args.local_path, '50gbfile.txt.out')
        rpath = args.remote_path + '/50gbfile.txt'

        if adl.exists(rpath, invalidate_cache=False):
            adl.rm(rpath)
        if os.path.exists(lpath_down):
            os.remove(lpath_down)

        result, elapsed = bench_upload_1_50gb(adl, lpath_up, rpath, config)
        if args.verify:
            verify(result)
        if result.successful:
            stats.setdefault('up-1-50gb', []).append(elapsed)

        result, elapsed = bench_download_1_50gb(adl, lpath_down, rpath, config)
        if args.verify:
            verify(result)
        if result.successful:
            stats.setdefault('down-1-50gb', []).append(elapsed)

        if args.validate:
            print(checksum(lpath_up), lpath_up)
            print(checksum(lpath_down), lpath_down)

        # Upload/download 50 1GB files

        lpath_up = os.path.join(args.local_path, '50_1GB_Files')
        lpath_down = os.path.join(args.local_path, '50_1GB_Files.out')
        rpath = args.remote_path + '/50_1GB_Files'

        if adl.exists(rpath):
            adl.rm(rpath, recursive=True)
        if os.path.exists(lpath_down):
            shutil.rmtree(lpath_down)

        result, elapsed = bench_upload_50_1gb(adl, lpath_up, rpath, config)
        if args.verify:
            verify(result)
        if result.successful:
            stats.setdefault('up-50-1gb', []).append(elapsed)

        result, elapsed = bench_download_50_1gb(adl, lpath_down, rpath, config)
        if args.verify:
            verify(result)
        if result.successful:
            stats.setdefault('down-50-1gb', []).append(elapsed)

        if args.validate:
            print(checksum(lpath_up), lpath_up)
            print(checksum(lpath_down), lpath_down)

    if args.statistics:
        print_summary_statistics(stats)
