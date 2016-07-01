#!/usr/bin/python
# test exec framework for multi-pipe
import time
import sys
from rsclib.execute import exitstatus, Method_Process, Exec_Process

def sleep () :
    time.sleep (300)
    for n, line in enumerate (sys.stdin) :
        if n < 4 :
            sys.stdout.write (line)
# end def sleep

# might look excessive but we want the cat to block and pipe buffers are
# huge these days:
args = ['/var/log/Xorg.0.log'] * 5000
args [0] = 'cat'
p1 = Exec_Process \
    ( cmd = '/bin/cat'
    , args = args
    )
p2 = Exec_Process (cmd = '/usr/bin/sort')
p3 = Exec_Process (cmd = '/usr/bin/uniq', args = ('/usr/bin/uniq', '-c'))
p4 = Method_Process (method = sleep)

p1.append (p2)
p2.append (p3)
p3.append (p4)

p1.run  ()
p1.wait ()

for p in (p1, p2, p3, p4) :
    if p.status :
        print exitstatus (p.name, p.status)
