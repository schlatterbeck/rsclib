#!/usr/bin/python
# Copyright (C) 2011-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from math import pi, log, sqrt

# According to Wikipedia
# https://de.wikipedia.org/wiki/Magnetische_Feldkonstante
# mu0 is no longer defined in terms of pi
# c is exact because the meter is defined by c
mu0  = 1.2566370621219e-6
c    = 299792458
eps0 = 1. / (mu0 * c**2)
#mu0  = 4e-7 * pi
#eps0 = 8.854187812813e-12

def cylindrical (l, r1, r2) :
    return 2 * pi * eps0 * l / log (r2 / float (r1))
# end def cylindrical

def parallel (d, A) :
    return eps0 * A / float (d)
# end def parallel

if __name__ == "__main__" :
    import sys
    print (c, mu0, eps0)
    print (cylindrical (0.109, 0.085 / 2.0, 0.098 / 2.0))
