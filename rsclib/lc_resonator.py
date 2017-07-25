#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014-17 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
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
