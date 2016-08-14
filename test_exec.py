#!/usr/bin/python
# test exec framework for multi-pipe
import time
from rsclib.execute import exitstatus, Method_Process, Exec_Process

def sleep () :
    time.sleep (5)
# end def sleep

p1 = Exec_Process \
    ( cmd = '/bin/cat'
    , args = \
        ( 'cat'
        , '/var/log/Xorg.0.log'
        , '/var/log/Xorg.0.log'
        , '/var/log/Xorg.0.log'
        )
    )
f  = open ('/tmp/sorted', 'w')
p2 = Exec_Process (cmd = '/usr/bin/sort', stdout = f)
p3 = Exec_Process (cmd = '/usr/bin/uniq')
p4 = Method_Process (method = sleep)

p1.append (p4)
p1.append (p2)
p1.append (p3)

p1.run  ()
p1.wait ()

for p in (p1, p2, p3, p4) :
    if p.status :
        print exitstatus (p.name, p.status)
