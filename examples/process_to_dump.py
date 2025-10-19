#!/usr/bin/env python3

def main():
    from os import getpid

    print(f'pid {getpid()}\n')
    del getpid

    i = 0

    from time import sleep
    while i < 100:
        i += 1
        print(i, end=' ', flush=True)
        sleep(1)

if __name__ == '__main__':
    main()
