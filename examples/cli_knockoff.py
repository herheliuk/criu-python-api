#!/usr/bin/env python3

if __name__ != '__main__':
    raise RuntimeError('Unsupported behaviour.')

import criu_api as criu
from os import (
    getpid as os_getpid,
    system as os_system
)

import readline

COMMANDS = [
    'wipe',
    'dump',
    'dump_stop',
    'full_dump',
    'dump_anyway',
    'restore',
    'kill_restore',
    'info',
    'clear',
    'quit'
]

def completer(text, state):
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return options[state] if state < len(options) else None

if input('criu.wipe() ?'):
    criu.wipe()

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
    
        if 'self' in _input_split:
            pids.add(os_getpid())
            _input_split.remove('self')
        
        if len(pids) == 1:
            new_pid = pids.pop()
            criu.set_pid(new_pid)
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
                criu.dump(allow_overwrite=False)
                print(f'dumped anyway. {criu._last_dump_number}')
            case 'restore' | 'r':
                criu.restore()
                print('restored.')
            case 'kill_restore' | 'kr':
                criu.restore(kill_if_exists=True)
                print('kill restored.')
            case 'info' | 'i':
                print(f'{os_getpid()=}\n{criu._pid=}\n{criu._min_dump_number=}\n{criu._last_dump_number=}\n{criu._track_mem=}')
            case 'quit' | 'q':
                exit()
            case _:
                print('*int* or self (sets pid)\n' + '\n'.join(COMMANDS))
except KeyboardInterrupt:
    print("\nKeyboardInterrupt")
