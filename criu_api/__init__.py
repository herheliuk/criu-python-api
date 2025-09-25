#!/usr/bin/env python3

from os import geteuid, makedirs, listdir, rmdir
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
            raise CRIUError(f"criu {' '.join(args)}\n{stderr}{stdout}".strip())
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

_pid: int = None

def set_pid(pid: int):
    '''Sets the target process ID.'''
    global _pid
    _pid = pid

_dumps_dir: Path = None
_min_dump_number: int = None
_last_dump_number: int = None

def _update_min_and_last_dump_number():
    global _last_dump_number, _min_dump_number
    dump_numbers = [int(dump_number) for dump_number in listdir(_dumps_dir) if dump_number.isdigit()] if _dumps_dir.exists() else None
    _min_dump_number = min(dump_numbers) if dump_numbers else 0
    _last_dump_number = max(dump_numbers) if dump_numbers else -1
    if dump_numbers:
        expected = set(range(_min_dump_number, _last_dump_number + 1))
        missing = expected - set(dump_numbers)
        if missing:
            raise FileNotFoundError(f"Missing dumps: {sorted(missing)}")

def set_dumps_dir(dumps_dir: str | Path = 'criu_dumps/'):
    '''Overrides the CRIU dumps directory.'''
    global _dumps_dir
    if isinstance(dumps_dir, str):
        _dumps_dir = Path(dumps_dir).resolve()
    elif isinstance(dumps_dir, Path):
        _dumps_dir = dumps_dir.resolve()
    else:
        raise TypeError(f"dumps_dir ({dumps_dir}) must be type of str or Path, not {type(dumps_dir).__name__}")
    
    _update_min_and_last_dump_number()

set_dumps_dir()

def clean_up(images_dir: Path = None):
    '''Removes the dump or dumps directory and all its contents.'''
    global _last_dump_number
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
        if not images_dir:
            _last_dump_number = -1

def _remove_dumps_from(dump_number: int):
    '''Removes the specified dump and all dumps after it'''
    for _dump_number in range(dump_number, _last_dump_number + 1):
        clean_up(_dumps_dir / str(_dump_number))

shell_job = True
tcp_established = True

def _no_pid_value_error():
    return ValueError(f'No pid was provided. Please use {__name__}.{set_pid.__name__}()')

def _get_pid_from_dump(dump_number: int) -> int:
    pids = set()
    for file_name in listdir(_dumps_dir / str(dump_number)):
        if "core-" in file_name:
            pids.add(int(file_name[len("core-"):-len(".img")]))
    
    if len(pids) == 1:
        return pids.pop()
    elif not pids:
        raise ValueError("No PIDs found.")
    else:
        raise ValueError(f'Unsupported behaviour; Too many PIDs: {pids}')

def dump(dump_number: int = None, leave_running = True, ensure_full_dump = False, allow_overwrite = False, additional_args: list[str] = None):
    '''Creates a full dump, or an incremental dump if memory tracking is available.'''
    global _last_dump_number
    if not _pid:
        if _last_dump_number == -1:
            raise _no_pid_value_error()
        last_pid = None
        try:
            last_pid = _get_pid_from_dump(_last_dump_number)
        except:
            raise _no_pid_value_error()
    if dump_number:
        if not isinstance(dump_number, int) or dump_number < 0:
            raise ValueError(f"Unsupported behaviour; dump_number ({repr(dump_number)}) must be an int >= {_min_dump_number}")
        if dump_number > _last_dump_number + 1:
            raise ValueError(f"Skipping dumps is not allowed; dump_number ({dump_number}) must be <= {_last_dump_number + 1}")
        if dump_number <= _last_dump_number:
            if allow_overwrite:
                if dump_number < _min_dump_number:
                    raise ValueError(f'Overwrite is out of range; dump_number ({dump_number}) must be >= {_min_dump_number}')
                else:
                    _remove_dumps_from(dump_number)
            else:
                raise FileExistsError(f'Overwrite prevented; dump_number ({dump_number}) already exists! Consider allow_overwrite=True')
    else:
        dump_number = _last_dump_number + 1
    images_dir = f'{_dumps_dir}/{dump_number}'
    makedirs(images_dir, exist_ok=allow_overwrite)
    args = [
        'dump',
        f'--images-dir={images_dir}',
        f'--tree={_pid or last_pid}',
    ]
    if leave_running:
        args.append('--leave-running')
    if shell_job:
        args.append('--shell-job')
    if tcp_established:
        args.append('--tcp-established')
    if _track_mem:
        args.append('--track-mem')
        if not ensure_full_dump and dump_number > _min_dump_number:
            args.append(f'--prev-images-dir=../{dump_number - 1}')
    if additional_args:
        args.extend(additional_args)
    try:
        old_last_dump_number = _last_dump_number
        _last_dump_number = dump_number
        return _criu(args)
    except:
        _last_dump_number = old_last_dump_number
        try:
            rmdir(images_dir)
        except:
            pass
        raise

def restore(dump_number: int = None, kill_if_exists = False, additional_args: list[str] = None):
    '''Restores the specified dump into the current terminal session.'''
    if not dump_number:
        if _last_dump_number >= 0:
            dump_number = _last_dump_number
        else:
            raise FileNotFoundError(f'No dumps to restore. Consider {__name__}.{_update_min_and_last_dump_number.__name__}()')
    if kill_if_exists:
        if not _pid:
            try:
                _pid = _get_pid_from_dump(dump_number)
            except:
                raise _no_pid_value_error()
        if pid_exists(_pid):
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
