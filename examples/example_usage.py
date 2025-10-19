#!/usr/bin/env python3

if __name__ != '__main__':
    raise RuntimeError('Unsupported behaviour.')

import criu_api as criu

from os import getpid as os_getpid

if input('criu.clean_up() ?'): criu.clean_up()

try:
    while True:
        _input = input('> ')
        match _input:
            case 'cl':
                criu.clean_up()
                print('cleaned up.')
            case 'fd':
                criu.dump(allow_overwrite=True)
                print(f'force dumped. {criu._last_dump_number}')
            case 'd':
                criu.dump()
                print(f'dumped. {criu._last_dump_number}')
            case 'ds':
                criu.dump(leave_running=False)
                print(f'dumped & stopped. {criu._last_dump_number}')
            case 'r':
                criu.restore()
                print('restored.')
            case 'kr':
                criu.restore(kill_if_exists=True)
                print('kill restored.')
            case 'q' | 'e':
                exit()
            case 'i':
                print(f'{os_getpid()=}\n{criu._pid=}\n{criu._min_dump_number=}\n{criu._last_dump_number=}\n{criu._track_mem=}')
            case _:
                try:
                    criu.set_pid(int(_input.strip()))
                except:
                    print('cl - clean_up\nfd - force dump\nd - dump\nds - dump & stop\nr - restore\nkr - kill & restore\ni - info\n*int* -> set_pid(x)\nq | e - exit()')
except KeyboardInterrupt:
    ...
except Exception as error:
    print(error)
