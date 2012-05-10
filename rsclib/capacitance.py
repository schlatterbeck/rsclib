#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from math import pi, log

c    = 299792458
mu0  = 4e-7 * pi
eps0 = 1. / (mu0 * c**2)

def cylindrical (l, r1, r2) :
    return 2 * pi * eps0 * l / log (r2 / float (r1))
# end def cylindrical

def parallel (d, A) :
    return eps0 * A / float (d)
# end def parallel

if __name__ == "__main__" :
    import sys
    print c, mu0, eps0
    print cylindrical (0.109, 0.085 / 2.0, 0.098 / 2.0)
