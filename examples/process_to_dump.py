#!/usr/bin/env python3

from os import getpid as os_getpid
from time import sleep as time_sleep

print(f'pid {os_getpid()}\n')

i = 0
    
while i < 60:
    i += 1
    print(i, end=' ', flush=True)
    time_sleep(1)
