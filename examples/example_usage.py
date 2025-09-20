#!/usr/bin/env python3

import criu_api as criu

#criu.set_dumps_dir("/tmp/criu_api_dumps")

input('criu.clean_up()') # DEBUG
criu.clean_up()

pid = None
while not pid:
    try:
        pid = int(input('pid to dump > '))
    except KeyboardInterrupt:
        exit()
    except:
        ...

print(f'criu.set_pid({pid=})')
criu.set_pid(pid)

try:
    input(f'criu.dump()') # DEBUG
    criu.dump()
    
    for i in range(1, 3):
        input(f'criu.dump({i=})') # DEBUG
        criu.dump(i)
    
    input(f'criu.dump(leave_running=False)') # DEBUG
    criu.dump(leave_running=False)
    
    input('criu.restore(3)') # DEBUG
    criu.restore(3)
except KeyboardInterrupt:
    ...
except Exception as error:
    print(error)
