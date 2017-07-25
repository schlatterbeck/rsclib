#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from math import pi, log

def L_s (l, d, n) :
    """ Inductance in µH for an air-cored cylindrical flat-winded coil
        of length l and diameter d with n windings.  Both l and d are in cm.
        The first publication that tried to give a formula for this type
        of coils is 
        Nagaoka, Hantaro (1909-05-06) "The Inductance Coefficients of
        Solenoids." 27. Journal of the College of Science, Imperial
        University, Tokyo, Japan. p. 18.
        http://www.g3ynh.info/zdocs/refs/Nagaoka1909.pdf
        Harold Wheeler later provided crude formulas for quick
        calculation in Wheeler, Harold A.;
        Simple Inductance Formulas for Radio Coils, Proceedings of the
        I.R.E., Vol. 16, No. 75, October 1928, pp. 1398-1400.
        but updated these formulas for much better accuracy -- and
        computer calculation in Wheeler, Harold A.; Inductance Formulas
        for Circular and Square Coils, Proceedings of the IEEE, Vol. 70,
        No. 12, December 1982, pp. 1449-1450.
        This is according to an optimized version of Wheelers formula
        by Robert Weaver in "Numerical Methods for Inductance Calculation"
        http://electronbunker.ca/CalcMethods3b.html (formula 35)
        where he used a solver to optimize the formula for low errors.
        Note: This is a current sheet formula, and will require round
        wire corrections for best accuracy.
    >>> print ("%2.2f" % L_s ( 0.8,   2,  10))
    2.33
    >>> print ("%2.2f" % L_s ( 1.6,   2,  20))
    6.30
    >>> print ("%2.2f" % L_s ( 4.0,   2,  50))
    20.19
    >>> print ("%2.2f" % L_s ( 8.0,   2, 100))
    44.49
    >>> print ("%2.2f" % L_s ( 2.0,   2,  10))
    1.36
    >>> print ("%2.2f" % L_s ( 4.0,   2,  20))
    3.23
    >>> print ("%2.2f" % L_s (10.0,   2,  50))
    9.08
    >>> print ("%2.2f" % L_s (20.0,   2, 100))
    18.93
    >>> print ("%2.2f" % L_s ( 0.8,  10,   10))
    21.46
    >>> print ("%2.2f" % L_s ( 8.0,  10,  100))
    787.20
    >>> print ("%2.2f" % L_s ( 0.8, 200,   10))
    805.22
    >>> print ("%2.2f" % L_s ( 8.0, 200,  100))
    51598.29
    """
    # original formula output in H, input in m
    # so we need to adjust for µH and cm (1e4 below)
    mu0 = 4e-7 * pi
    u   = float (d) / float (l)
    return mu0 / 2.0 * 1e4 * d * n**2 * \
        ( log (1.0 + (pi / 2.0) * u)
        + 1.0
          / ( (1. / (log (8. / pi) - 0.5))
            + 3.437 / u
            + (24. / (3. * pi**2 - 16)) / (u ** 2)
            - 0.47 / ((0.755 + u) ** 1.44)
            )
        )
# end def L_s

def k_s (pitch, diameter) :
    """ Self inductance correction for round wire """
    return (5. / 4.) - log ((2 * pitch) / diameter)
# end def k_s

def k_m (n) :
    """ Mutual inductance correction for round wire """
    return ( log (2 * pi)
           - 1.5
           - (log (n) / (6 * n))
           - (0.33084236 / n)
           - (1.0 / (120. * n**3))
           + (1.0 / (504. * n**5))
           - (0.0011923 / n**7)
           + (0.0005068 / n**9)
           )
# end def k_m

def delta_roundwire (r, n, pitch, diameter) :
    """ Round wire correction according to Rosa, Edward B.;
        Calculation of the Self-Inductance of Single-Layer Coils,
        NBS Bulletin, Vol. 2, No. 2, 1907.
        This was later adapted for computer calculation by Robert
        Weaver, Weaver, Robert; Investigation of E.B. Rosa's Round Wire
        Mutual Inductance Correction Formula, July 2008.
        Documentation taken from
        http://electronbunker.ca/CalcMethods2a.html
        n is the number of turns, r is the coil radius.
        The winding pitch and conductor diameter are in cm.
    >>> print ("%2.5f" % delta_roundwire (1,  10, 0.080, 0.05))
    0.04439
    >>> print ("%2.5f" % delta_roundwire (1,  20, 0.080, 0.05))
    0.09631
    >>> print ("%2.5f" % delta_roundwire (1,  50, 0.080, 0.05))
    0.25451
    >>> print ("%2.5f" % delta_roundwire (1, 100, 0.080, 0.05))
    0.51992
    >>> print ("%2.5f" % delta_roundwire (1,  10, 0.200, 0.05))
    -0.07075
    >>> print ("%2.5f" % delta_roundwire (1,  20, 0.200, 0.05))
    -0.13398
    >>> print ("%2.5f" % delta_roundwire (1,  50, 0.200, 0.05))
    -0.32121
    >>> print ("%2.5f" % delta_roundwire (1, 100, 0.200, 0.05))
    -0.63152
    >>> print ("%2.5f" % delta_roundwire (  5,  10, 0.080, 0.05))
    0.22196
    >>> print ("%2.5f" % delta_roundwire (  5, 100, 0.080, 0.05))
    2.59962
    >>> print ("%2.5f" % delta_roundwire (100,  10, 0.080, 0.05))
    4.43916
    >>> print ("%2.5f" % delta_roundwire (100, 100, 0.080, 0.05))
    51.99242
    """
    return 0.004 * pi * r * n * (k_s (pitch, diameter) + k_m (n))
# end def delta_roundwire

def induction (d, n, diameter, l = 0, pitch = 0) :
    """ induction with round-wire correction
    >>> print ("%2.2f" % induction (  2,  10, 0.05, l =  0.8))
    2.28
    >>> print ("%2.2f" % induction (  2,  20, 0.05, l =  1.6))
    6.20
    >>> print ("%2.2f" % induction (  2,  50, 0.05, l =  4.0))
    19.93
    >>> print ("%2.2f" % induction (  2, 100, 0.05, l =  8.0))
    43.97
    >>> print ("%2.2f" % induction (  2,  10, 0.05, l =  2.0))
    1.43
    >>> print ("%2.2f" % induction (  2,  20, 0.05, l =  4.0))
    3.36
    >>> print ("%2.2f" % induction (  2,  50, 0.05, l = 10.0))
    9.40
    >>> print ("%2.2f" % induction (  2, 100, 0.05, l = 20.0))
    19.56
    >>> print ("%2.2f" % induction ( 10,  10, 0.05, l =  0.8))
    21.24
    >>> print ("%2.2f" % induction ( 10, 100, 0.05, l =  8.0))
    784.60
    >>> print ("%2.2f" % induction (200,  10, 0.05, l =  0.8))
    800.78
    >>> print ("%2.2f" % induction (200, 100, 0.05, l =  8.0))
    51546.30
    >>> print ("%2.2f" % induction (  2,  10, 0.05, pitch = 0.08))
    2.28
    """
    if l :
        pitch = float (l) / float (n)
    elif pitch :
        l = float (pitch) * float (n)
    else :
        raise ValueError ("l or pitch must be != 0")
    return L_s (l, d, n) - delta_roundwire (d / 2.0, n, pitch, diameter)
# end def induction

if __name__ == "__main__" :
    import sys
    if len (sys.argv) != 5 :
        print >> sys.stderr \
            , "Usage: %s diameter windings wirediameter pitch" % sys.argv [0]
        sys.exit (23)
    args = [float (i) for i in sys.argv [1:]]
    print (induction (*args [:3], pitch = args [3]))
