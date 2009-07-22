#!/usr/bin/python
# test exec framework for multi-pipe
from rsclib.execute import exitstatus, Method_Process, Exec_Process

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
p3 = p2
p3 = Exec_Process (cmd = '/usr/bin/head')

p1.append (p2)
p1.append (p3)

p1.run  ()
p1.wait ()

for p in (p1, p2, p3) :
    if p.status :
        print exitstatus (p.name, p.status)
