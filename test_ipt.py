#!/usr/bin/python

import sys
from rsclib.trafficshape import IPTables_Mangle_Rule

f = None
if len (sys.argv) > 1 :
    f = open (sys.argv [1])
IPTables_Mangle_Rule.parse_prerouting_rules (f)
for r in IPTables_Mangle_Rule.rules :
    print r.as_iptables ()
