#!/usr/bin/env python3

if __name__ != '__main__':
    raise RuntimeError('Unsupported behaviour.')

import criu_api as criu
from os import (
    getpid as os_getpid,
    fork as os_fork,
    waitpid as os_waitpid,
    system as os_system
)
from sys import exit as sys_exit

_mem_file = 'mem.txt'

def write_mem(info: str):
    with open(_mem_file, 'w') as file:
        file.write(info)
        
def pop_mem() -> str:
    with open(_mem_file, 'r') as file:
        info = file.read()
    write_mem('')
    return info

child_pid = os_fork()
if child_pid > 0:
    os_waitpid(child_pid, 0)
    while True:
        
        info = pop_mem()
        
        try:
            int(info)
        except:
            exit()

        try:
            criu.restore(int(info))
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            exit()
        except Exception as e:
            print(e)
            exit()

import readline

COMMANDS = [
    'wipe',
    'dump',
    'dump_stop',
    'full_dump',
    'dump_anyway',
    'restore',
    'kill_restore',
    'self_restore',
    'info',
    'clear',
    'quit'
]

def completer(text, state):
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return options[state] if state < len(options) else None

readline.set_completer(completer)
readline.parse_and_bind('tab: complete')

try:
    while True:
        _input = input('> ').strip()

        readline.add_history(_input)
            
        pids = set()
        
        _input_split = _input.split()
        
        for word in _input_split:
            try:
                pids.add(int(word))
            except:
                pass
        
        for pid in pids:
            _input_split.remove(str(pid))
        
        new_pid = -1
        
        if len(pids) == 1:
            new_pid = pids.pop()
            criu.set_pid(new_pid)
            if not 'sr' in _input and not 'self_restore' in _input:
                print(f'pid is set to {new_pid}.')
        elif len(pids) > 1:
            raise ValueError(f'Too many PIDs: {pids}')
        
        _input = ' '.join(_input_split)
        
        if not _input:
            continue
        
        match _input:
            case 'clear' | 'c':
                os_system('clear')
            case 'wipe' | 'w':
                criu.wipe()
                print('wiped.')
            case 'dump' | 'd':
                criu.dump()
                print(f'dumped. {criu._last_dump_number}')
            case 'dump_stop' | 'ds':
                criu.dump(leave_running=False)
                print(f'dumped & stopped. {criu._last_dump_number}')
            case 'full_dump' | 'fd':
                criu.dump(ensure_full_dump=False)
                print(f'full dumped. {criu._last_dump_number}')
            case 'dump_anyway' | 'da':
                # if there was an error during normal dump, there will be leftover files. With this functioon you can overwrite them.
                criu.dump(allow_overwrite=True)
                print(f'dumped anyway. {criu._last_dump_number}')
            case 'restore' | 'r':
                criu.restore()
            case 'self_restore' | 'sr':
                print(f'self restoring... {new_pid if new_pid >= 0 else criu._last_dump_number}')
                write_mem(str(new_pid if new_pid >= 0 else criu._last_dump_number))
                sys_exit()
            case 'kill_restore' | 'kr':
                print('kill restoring...')
                criu.restore(kill_if_exists=True)
            case 'info' | 'i':
                print(f'{os_getpid()=}\n{criu._pid=}\n{criu._min_dump_number=}\n{criu._last_dump_number=}\n{criu._track_mem=}')
            case 'quit' | 'q':
                write_mem('exit')
                exit()
            case _:
                print('*int* (sets pid)\n' + '\n'.join(COMMANDS))
except KeyboardInterrupt:
    print("\nKeyboardInterrupt")
