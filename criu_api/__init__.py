#!/usr/bin/env python3

from os import geteuid, makedirs
from sys import exit, executable, argv
from platform import system
from subprocess import Popen, run, PIPE

if system() != "Linux":
    raise RuntimeError('Unsupported operating system.')

if geteuid() != 0:
    run(['sudo', executable] + argv)
    exit()

del system, geteuid, executable, argv

from pathlib import Path
from re import escape
from shutil import rmtree
from psutil import pid_exists, Process

class CRIUError(Exception):
    """Custom exception for CRIU-related errors."""

def _criu(args: list):
    """Executes a CRIU command with the given arguments."""
    process = None
    try:
        process = Popen(['criu'] + args, stdout=PIPE, stderr=PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise CRIUError(f"{' '.join(args)}\n{stderr}{stdout}".strip())
        return stdout.rstrip('\n')
    except KeyboardInterrupt:
        process.terminate()
        raise

_track_mem = False

def _health_check(args_to_check: list[str] = []):
    '''Verifies that CRIU is available and sets memory tracking.'''
    global _track_mem
    try:
        result = _criu(['check', '--track-mem'])
        _track_mem = True
        return result
    except:
        _track_mem = False
    return _criu(['check'] + args_to_check)

_health_check()

_pid = None

def set_pid(pid: int):
    '''Sets the target process ID.'''
    global _pid
    _pid = pid

_dumps_dir = None

def set_dumps_dir(dumps_dir: str | Path = 'criu_dumps/'):
    '''Overrides the CRIU dumps directory.'''
    global _dumps_dir
    if isinstance(dumps_dir, str):
        _dumps_dir = Path(dumps_dir).resolve()
    elif isinstance(dumps_dir, Path):
        _dumps_dir = dumps_dir.resolve()
    else:
        raise TypeError(f"dumps_dir must be str or Path, not {type(dumps_dir).__name__}!")

set_dumps_dir()

def clean_up(images_dir: Path = None):
    '''Removes the dump or dumps directory and all its contents.'''
    target_dir = images_dir or _dumps_dir
    if target_dir.exists():
        try:
            rmtree(target_dir)
        except PermissionError:
            result = run(f"mount | grep -E '{escape(str(target_dir))}/.*/\\.criu\\.cgyard'", shell=True, capture_output=True, text=True)
            criu_mounts = [line.split()[2] for line in result.stdout.strip().splitlines()]
            for mnt in reversed(criu_mounts):
                run(["umount", "-l", mnt], check=True)
            rmtree(target_dir)

_last_dump_number = -1

def _remove_dumps_from(dump_number: int):
    '''Removes the specified dump and all dumps after it'''
    for _dump_number in range(dump_number, _last_dump_number + 1):
        clean_up(_dumps_dir / str(_dump_number))

shell_job = True
tcp_established = True

def _no_pid_warning():
    return f'No pid was provided; use {__name__}.set_pid().'

def dump(dump_number: int = None, leave_running = True, allow_overwrite = False, additional_args: list[str] = None):
    '''Creates a full dump, or an incremental dump if memory tracking is available.'''
    if not _pid:
        raise Exception(_no_pid_warning())
    global _last_dump_number
    not_overwritten = True
    if dump_number:
        if not isinstance(dump_number, int) or dump_number < 0:
            raise ValueError(f'dump_number should be int >= 0.')
        if dump_number <= _last_dump_number:
            if allow_overwrite:
                _remove_dumps_from(dump_number)
                not_overwritten = False
            else:
                raise Exception(f'dump {dump_number} already exists! consider using allow_overwrite=True.')
    else:
        dump_number = _last_dump_number + 1
    _last_dump_number = dump_number
    images_dir = f'{_dumps_dir}/{dump_number}'
    makedirs(images_dir)
    args = [
        'dump',
        f'--images-dir={images_dir}',
        f'--tree={_pid}',
    ]
    if leave_running:
        args.append('--leave-running')
    if shell_job:
        args.append('--shell-job')
    if tcp_established:
        args.append('--tcp-established')
    if _track_mem and dump_number > 0 and not_overwritten:
        args.extend([
            f'--prev-images-dir=../{dump_number - 1}',
            '--track-mem'
        ])
    if additional_args:
        args.extend(additional_args)
    return _criu(args)

def restore(dump_number: int, kill_if_exists = False, additional_args: list[str] = None):
    '''Restores the specified dump into the current terminal session.'''
    if kill_if_exists:
        if not _pid:
            raise Exception(_no_pid_warning())
        elif pid_exists(_pid):
            Process(_pid).kill()
    args = [
        'restore',
        f'--images-dir={_dumps_dir}/{dump_number}',
    ]
    if shell_job:
        args.append('--shell-job')
    if tcp_established:
        args.append('--tcp-established')
    if _track_mem:
        args.append('--track-mem')
    if additional_args:
        args.extend(additional_args)
    return _criu(args)
