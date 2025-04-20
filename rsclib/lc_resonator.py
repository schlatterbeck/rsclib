#!/usr/bin/python
# Copyright (C) 2014-17 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ****************************************************************************

from __future__ import print_function
from math import pi, sqrt

def f_l_c (l, c) :
    """ calculate frequency from given L and C.
    >>> print ("%7.2f" % f_l_c (37e-6, 200e-12))
    1850138.63
    """
    return 1. / (2 * pi * sqrt (l * c))
# end def  f_l_c

def c_f_l (f, l) :
    """ calculate capacitance from given f and L.
    >>> print ("%7.2e" % c_f_l (1.85e6, 37e-6))
    2.00e-10
    """
    return 1. / (4 * pi**2 * l * f**2)
# end def c_f_l

def l_f_c (f, c) :
    """ calculate capacitance from given f and C.
    >>> print ("%7.2e" % c_f_l (1.85e6, 200e-12))
    3.70e-05
    """
    return c_f_l (f, c)
# end def c_f_l

if __name__ == "__main__" :
    import sys
