#!/usr/bin/env python3

# criu from Oct 19, 2025
# intermittent issue on first ever run

dumps_dir = './criu_dumps/'

from pycriu import criu as pycriu_criu
from shutil import which as shutil_which
from os import (
    open as os_open,
    close as os_close,
    O_DIRECTORY as os_O_DIRECTORY,
    makedirs as os_makedirs
)
from contextlib import contextmanager

@contextmanager
def open_directory_fd(dir_path: str):
    fd = os_open(dir_path, os_O_DIRECTORY)
    try:
        yield fd
    finally:
        os_close(fd)

criu_binary = shutil_which('criu')

print(f'{dumps_dir=}')
print(f'{criu_binary=}\n')

criu = pycriu_criu()
criu.use_binary(criu_binary)

pid = int(input('Please enter pid to dump: '))

criu.opts.pid = pid
criu.opts.shell_job = True

os_makedirs(dumps_dir, exist_ok=True)

with open_directory_fd(dumps_dir) as fd:
    criu.opts.images_dir_fd = fd
    criu.dump()

print(f'\nSuccessfully dumped {pid}.')
