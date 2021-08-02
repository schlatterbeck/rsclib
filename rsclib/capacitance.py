#!/usr/bin/python
# Copyright (C) 2011-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
