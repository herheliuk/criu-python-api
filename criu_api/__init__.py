#!/usr/bin/env python3

"""
Authors: Andrii Herheliuk
Licence: MIT (CRIU is GPLv2)
"""

try:
    from pycriu import (
        criu as pycriu_criu,
        rpc as pycriu_rpc
    )
except:
    raise RuntimeError('[pycriu is not available] Please activate your env or compile & install pycriu.')

from os import (
    makedirs as os_makedirs,
    listdir as os_listdir,
    geteuid as os_geteuid,
    uname as os_uname,
    getpid as os_getpid
)

from sys import argv as sys_argv

if os_geteuid() != 0:
    raise PermissionError(f'[requires escalated privileges] Please run "sudo -E $(which python) {sys_argv[0]}"')

from psutil import (
    Process as psutil_Process,
    pid_exists as psutil_pid_exists
)

from shutil import (
    rmtree as shutil_rmtree
)
from subprocess import run as subprocess_run
from time import sleep

from contextlib import contextmanager
from pathlib import Path

shell_job: bool = True
tcp_established: bool = True

_dumps_directory: str = None
_min_dump_number: int = None
_last_dump_number: int = None
_pid: int = None

_track_mem: bool = os_uname().machine == 'x86_64'

def _kill_process(pid: int):
    psutil_Process(pid).kill()
    while psutil_pid_exists(pid):
        sleep(.1)

def _update_min_and_last_dump_number():
    global _last_dump_number, _min_dump_number
    dump_numbers = None
    
    if _dumps_directory.exists():
        dump_numbers = [int(dump_number) for dump_number in os_listdir(_dumps_directory) if dump_number.isdigit()]
    
    _min_dump_number = min(dump_numbers) if dump_numbers else 0
    _last_dump_number = max(dump_numbers) if dump_numbers else -1
    
    if dump_numbers:
        expected = set(range(_min_dump_number, _last_dump_number + 1))
        missing = expected - set(dump_numbers)
        if missing:
            raise FileNotFoundError(f"Missing dumps: {sorted(missing)}")

def set_dumps_dir(dumps_directory: str | Path = './criu_dumps/'):
    global _dumps_directory
    if isinstance(dumps_directory, str):
        _dumps_directory = Path(dumps_directory).resolve()
    elif isinstance(dumps_directory, Path):
        _dumps_directory = dumps_directory.resolve()
    else:
        raise TypeError(f"dumps_directory ({_dumps_directory}) must be type of str or Path, not {type(_dumps_directory).__name__}")
    
    _update_min_and_last_dump_number()

def ensure_dumps_dir(func):
    def wrapper(*args, **kwargs):
        if not _dumps_directory:
            set_dumps_dir()
        globals()[func.__name__] = func
        return func(*args, **kwargs)
    return wrapper

@ensure_dumps_dir
def wipe(images_dir: Path = None):
    '''Removes the dump or dumps directory and all its contents!'''
    global _last_dump_number
    target_dir = images_dir or _dumps_directory
    if target_dir.exists():
        try:
            shutil_rmtree(target_dir)
        except PermissionError:
            result = subprocess_run(
                ["mount"], capture_output=True, text=True
            )
            criu_mounts = [
                line.split()[2]
                for line in result.stdout.splitlines()
                if f"{target_dir}/" in line and ".criu.cgyard" in line
            ]
            for mnt in reversed(criu_mounts):
                subprocess_run(["umount", "-l", mnt], check=True)
            
            shutil_rmtree(target_dir)
        if not images_dir:
            _last_dump_number = -1

def check(features: list[str] = None):
    if not features:
        features = []
    
    if _track_mem:
        features.append('mem_dirty_track')
    
    for feature in features:
        subprocess_run([
            'criu', 'check', '--feature', feature
        ], check=True)
        
    else:
        subprocess_run([
            'criu', 'check'
        ], check=True)

def set_pid(pid: int | str):
    '''Used to let functions know which process to work with.'''
    global _pid
    if pid == os_getpid():
        _pid = None
    else:
        _pid = int(pid)

def _no_pid_value_error():
    return ValueError(f'No pid was provided. Please use {set_pid.__name__}()')

def _get_pid_from_dump(dump_number: int) -> int:
    pids = set()
    for file_name in os_listdir(_dumps_directory / str(dump_number)):
        if "core-" in file_name:
            pids.add(int(file_name[len("core-"):-len(".img")]))
    
    if len(pids) == 1:
        return pids.pop()
    elif not pids:
        raise ValueError("No PIDs found.")
    else:
        raise ValueError(f'[Unsupported behaviour] Too many PIDs: {pids}')

def _remove_dumps_from(dump_number: int):
    '''Removes the specified dump and all dumps after it, used to overwrite the history.'''
    for _dump_number in range(dump_number, _last_dump_number + 1):
        wipe(_dumps_directory / str(_dump_number))

@ensure_dumps_dir
def dump(dump_number: int = None, leave_running = True, ensure_full_dump = False, allow_overwrite = False, additional_args: dict[str, any] = None):
    '''Creates a full dump, or an incremental dump if memory tracking is available.'''
    global _last_dump_number
    
    if dump_number:
        if not isinstance(dump_number, int) or dump_number < 0:
            raise ValueError(f"[Unsupported behaviour] dump_number ({repr(dump_number)}) must be an int >= {_min_dump_number}")
        if dump_number > _last_dump_number + 1:
            raise ValueError(f"[Skipping dumps is not allowed] dump_number ({dump_number}) must be <= {_last_dump_number + 1}")
        if dump_number <= _last_dump_number:
            if allow_overwrite:
                if dump_number < _min_dump_number:
                    raise ValueError(f'[Overwrite is out of range] dump_number ({dump_number}) must be >= {_min_dump_number}')
                else:
                    _remove_dumps_from(dump_number)
            else:
                raise FileExistsError(f'[Overwrite prevented] dump_number ({dump_number}) already exists! Consider allow_overwrite=True')
    else:
        dump_number = _last_dump_number + 1
    
    images_dir = f'{_dumps_directory}/{dump_number}'
    os_makedirs(images_dir, exist_ok=allow_overwrite)
    
    criu = pycriu_criu()

    criu.opts = pycriu_rpc.criu_opts(
        pid=_pid,
        leave_running=leave_running,
        shell_job=shell_job,
        tcp_established=tcp_established,
        track_mem=_track_mem,
        images_dir_fd=-1,
        images_dir=images_dir,
        parent_img=(
            f'../{dump_number - 1}'
            if _track_mem and not ensure_full_dump and dump_number > _min_dump_number
            else None
        ),
        **(additional_args or {})
    )

    _old_value = _last_dump_number
    try:
        _last_dump_number = dump_number
        try:
            criu.dump()
        except: # first time using binary might give an error
            criu.dump()
    except:
        _last_dump_number = _old_value
        raise

@ensure_dumps_dir
def restore(dump_number: int = None, kill_if_exists = False, other_cmd_args: list[str] = None):
    '''Restores the specified dump into the current terminal session.'''
    if not dump_number:
        if _last_dump_number >= 0:
            dump_number = _last_dump_number
        else:
            raise FileNotFoundError(f'No dumps to restore. Consider {__name__}.{_update_min_and_last_dump_number.__name__}()')
    
    if kill_if_exists:
        if not _pid:
            try:
                implied_pid = _get_pid_from_dump(dump_number)
            except:
                raise _no_pid_value_error()
        
        if psutil_pid_exists(_pid or implied_pid):
            _kill_process(_pid or implied_pid)
    
    args = other_cmd_args or []
    
    if shell_job:
        args.append('--shell-job')
    if tcp_established:
        args.append('--tcp-established')
    if _track_mem:
        args.append('--track-mem')
        
    subprocess_run([
        'criu', 'restore',
        '--images-dir', f'{_dumps_directory}/{dump_number}',
        *args
    ], check=True)
