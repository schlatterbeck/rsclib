#!/usr/bin/python

from rsclib.trafficshape import IPTables_Mangle_Rule

IPTables_Mangle_Rule.parse_prerouting_rules (open ('prerouting.out'))
for r in IPTables_Mangle_Rule.rules :
    print r.as_iptables ()
