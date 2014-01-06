#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from math import pi, sqrt

def f_l_c (l, c) :
    """ calculate frequency from given L and C.
    >>> print "%7.2f" % f_l_c (37e-6, 200e-12)
    1850138.63
    """
    return 1. / (2 * pi * sqrt (l * c))
# end def  f_l_c

def c_f_l (f, l) :
    """ calculate capacitance from given f and L.
    >>> print "%7.2e" % c_f_l (1.85e6, 37e-6)
    2.00e-10
    """
    return 1. / (4 * pi**2 * l * f**2)
# end def c_f_l

def l_f_c (f, c) :
    """ calculate capacitance from given f and C.
    >>> print "%7.2e" % c_f_l (1.85e6, 200e-12)
    3.70e-05
    """
    return c_f_l (f, c)
# end def c_f_l

if __name__ == "__main__" :
    import sys
