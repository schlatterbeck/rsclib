#!/usr/bin/python
# test exec framework for multi-pipe
import time
import sys
from rsclib.execute import exitstatus, Method_Process, Exec_Process

p1 = Exec_Process \
    ( cmd = '/bin/cat'
    , args = ('cat', '/etc/passwd')
    )
p2 = Exec_Process \
    ( cmd = '/usr/bin/head'
    , args = ('head', '-n', '1')
    , stdout = 'PIPE'
    , stderr = 'PIPE'
    )
p3 = Exec_Process \
    ( cmd = '/usr/bin/tail'
    , args = ('tail', '-n', '1')
    , stdout = 'PIPE'
    , stderr = 'PIPE'
    )

p1.append (p2)
p1.append (p3)

stdout, stderr = p1.communicate ()

print "STDOUT"
print stdout,
print "STDERR"
print stderr,

for p in (p1, p2, p3) :
    if p.status :
        print exitstatus (p.name, p.status)
