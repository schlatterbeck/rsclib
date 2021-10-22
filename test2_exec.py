#!/usr/bin/python3
# test exec framework for multi-pipe
import sys
from rsclib.execute import exitstatus, Method_Process, Exec_Process

def reader () :
    for line in sys.stdin :
        print ("%5d:" % len(line), line.rstrip ())

def writer () :
    print (1,2,3,4,5,6,7,8)
    print ("huhu")


p1 = Method_Process (method = writer, args = ('cat', '/etc/passwd'))
f  = open ('/tmp/sorted', 'w')
p2 = Method_Process (method = reader)#, stdout = f)

p1.append (p2)

p1.run  ()
p1.wait ()

for p in (p1, p2) :
    if p.status :
        print (exitstatus (p.name, p.status))
