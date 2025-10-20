import criu_api as criu

if input('criu.wipe() ?'):
    criu.wipe()

pid = int(input('pid: ').strip())

criu.set_pid(pid)

i = 0

while True:
    criu.dump()
    i+=1
    print(i)

""" ARM
criu_api via cli -> process_to_dump.py

~44 seconds ~5800 dumps ~22G (no track mem)

~120 dumps/second. this is Terrifying...

"""

""" slow VM
criu_api via cli -> process_to_dump.py

~55 seconds ~208 dumps ~26M (track mem)

~3.5 dumps/second. (29x smaller files)

"""
