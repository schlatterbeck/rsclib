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

mu0 = 4e-7 * pi

def A (d) :
    """ Area from diameter d
    >>> print ("%2.2f" % A (10))
    78.54
    """
    return pi * (d/2.0) ** 2

def L_s (l, d, n) :
    """ Inductance in µH for an air-cored cylindrical flat-winded coil
        of length l and diameter d with n windings.  Both l and d are in m.
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
        Checked against http://electronbunker.ca/eb/InductanceCalc.html
        we have some rounding errors compared to the javascript
        implementation.
    >>> print ("%2.4f" % (L_s (0.008, 0.02,  10) * 1e6))
    2.3286
    >>> print ("%2.4f" % (L_s (0.016, 0.02,  20) * 1e6))
    6.2976
    >>> print ("%2.4f" % (L_s (0.04,  0.02,  50) * 1e6))
    20.1871
    >>> print ("%2.4f" % (L_s (0.08,  0.02, 100) * 1e6))
    44.4944
    >>> print ("%2.4f" % (L_s (0.02,  0.02,  10) * 1e6))
    1.3589
    >>> print ("%2.4f" % (L_s (0.04,  0.02,  20) * 1e6))
    3.2299
    >>> print ("%2.4f" % (L_s (0.1,   0.02,  50) * 1e6))
    9.0808
    >>> print ("%2.4f" % (L_s (0.2,   0.02, 100) * 1e6))
    18.9258
    >>> print ("%2.4f" % (L_s (0.008, 0.1,   10) * 1e6))
    21.4590
    >>> print ("%2.4f" % (L_s (0.08,  0.1,  100) * 1e6))
    787.2003
    >>> print ("%2.4f" % (L_s (0.008, 2,     10) * 1e6))
    805.2205
    >>> print ("%2.2f" % (L_s (0.08,  2,    100) * 1e6))
    51598.29
    """
    u   = float (d) / float (l)
    return mu0 * d * n**2 * 0.5 * \
        ( log (1.0 + (pi / 2.0) * u)
        + 1.0
          / ( (1. / (log (8. / pi) - 0.5))
            + 3.437 / u
            + (24. / (3. * pi**2 - 16)) / (u ** 2)
            - 0.47 / ((0.755 + u) ** 1.44)
            )
        )
# end def L_s

def k_s (pitch, d_w) :
    """ Self inductance correction for round wire
        See http://electronbunker.ca/eb/CalcMethods2a.html
        d_w is the wire diameter, pitch is the distance between the
        middle of two windings.
        Note that since the output is dimensionless, pitch and d_w must
        just be given in the same units (e.g. m, cm, mm, ..)
    >>> print ("%2.4f" % k_s (3, 0.0012))
    -7.2672
    >>> print ("%2.4f" % k_s (0.3, 0.0012))
    -4.9646
    >>> print ("%2.4f" % k_s (0.003, 0.0012))
    -0.3594
    """
    return (5. / 4.) - log ((2 * pitch) / d_w)
# end def k_s

def k_m (n) :
    """ Mutual inductance correction for round wire
        This is the part the just depends on the number of windings n
        See http://electronbunker.ca/eb/CalcMethods2a.html
    >>> print ("%1.5f" % k_m (1))
    0.00000
    >>> print ("%1.5f" % k_m (10))
    0.26641
    >>> print ("%1.5f" % k_m (50))
    0.31822
    >>> print ("%1.5f" % k_m (100))
    0.32689
    """
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

def delta_roundwire (r, n, pitch, d_w) :
    """ Round wire correction according to Rosa, Edward B.;
        Calculation of the Self-Inductance of Single-Layer Coils,
        NBS Bulletin, Vol. 2, No. 2, 1907.
        This was later adapted for computer calculation by Robert
        Weaver, Weaver, Robert; Investigation of E.B. Rosa's Round Wire
        Mutual Inductance Correction Formula, July 2008.
        Documentation taken from
        http://electronbunker.ca/CalcMethods2a.html
        n is the number of turns, r is the coil radius in meter (m).
        The winding pitch and conductor diameter d_w are in the same unit
        (e.g., m, cm, ...). Output is in Farad (F)
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  10, 0.080, 0.05)))
    0.04439
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  20, 0.080, 0.05)))
    0.09631
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  50, 0.080, 0.05)))
    0.25451
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01, 100, 0.080, 0.05)))
    0.51992
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  10, 0.200, 0.05)))
    -0.07075
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  20, 0.200, 0.05)))
    -0.13398
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01,  50, 0.200, 0.05)))
    -0.32121
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.01, 100, 0.200, 0.05)))
    -0.63152
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.05,  10, 0.080, 0.05)))
    0.22196
    >>> print ("%2.5f" % (1e6 * delta_roundwire (0.05, 100, 0.080, 0.05)))
    2.59962
    >>> print ("%2.5f" % (1e6 * delta_roundwire (1,     10, 0.080, 0.05)))
    4.43916
    >>> print ("%2.5f" % (1e6 * delta_roundwire (1,    100, 0.080, 0.05)))
    51.99242
    """
    return 4e-7 * pi * r * n * (k_s (pitch, d_w) + k_m (n))
# end def delta_roundwire

def induction (d, n, d_w, l = 0, pitch = 0) :
    """ induction with round-wire correction
        d (diameter of coil) and (optional) l in m, either l or pitch
        must be specified.
        The parameter d_w is the diameter of the wire in m.
        Inductance is returned in H.
        See http://electronbunker.ca/eb/CalcMethods3b.html
        and http://electronbunker.ca/eb/CalcMethods2a.html
        cross-checked against online calculator at
        http://electronbunker.ca/eb/InductanceCalc.html
        We have some rounding errors compared to the javascript
        implementation.
    >>> print ("%2.4f" % (induction (0.02,  10, 0.0005, l = 0.008) * 1e6))
    2.2842
    >>> print ("%2.4f" % (induction (0.02,  20, 0.0005, l = 0.016) * 1e6))
    6.2013
    >>> print ("%2.4f" % (induction (0.02,  50, 0.0005, l = 0.04)  * 1e6))
    19.9326
    >>> print ("%2.4f" % (induction (0.02, 100, 0.0005, l = 0.08)  * 1e6))
    43.9745
    >>> print ("%2.4f" % (induction (0.02,  10, 0.0005, l = 0.02)  * 1e6))
    1.4296
    >>> print ("%2.4f" % (induction (0.02,  20, 0.0005, l = 0.04)  * 1e6))
    3.3639
    >>> print ("%2.4f" % (induction (0.02,  50, 0.0005, l = 0.1)   * 1e6))
    9.4020
    >>> print ("%2.4f" % (induction (0.02, 100, 0.0005, l = 0.2)   * 1e6))
    19.5573
    >>> print ("%2.4f" % (induction (0.1,   10, 0.0005, l = 0.008) * 1e6))
    21.2370
    >>> print ("%2.4f" % (induction (0.1,  100, 0.0005, l = 0.08)  * 1e6))
    784.6007
    >>> print ("%2.4f" % (induction (2,     10, 0.0005, l = 0.008) * 1e6))
    800.7814
    >>> print ("%2.2f" % (induction (2,    100, 0.0005, l = 0.08)  * 1e6))
    51546.30
    >>> print ("%2.4f" % (induction (2,     10, 0.0005, pitch = 0.008) * 1e6))
    540.4789
    """
    if l :
        pitch = float (l) / float (n)
    elif pitch :
        l = float (pitch) * float (n)
    else :
        raise ValueError ("l or pitch must be != 0")
    return L_s (l, d, n) - delta_roundwire (d / 2.0, n, pitch, d_w)
# end def induction

def wikipedia_long_coil (n, d, l) :
    """ Long coil according to wikipedia
        https://de.wikipedia.org/wiki/Zylinderspule
        https://en.wikipedia.org/wiki/Solenoid#Inductance
    >>> print ("%2.4f" % (wikipedia_long_coil ( 33, 0.04, 0.08) * 1e6))
    21.4960
    >>> print ("%2.4f" % (wikipedia_long_coil ( 33, 0.04, 0.16) * 1e6))
    10.7480
    >>> print ("%2.4f" % (wikipedia_long_coil ( 33, 0.04, 0.32) * 1e6))
    5.3740
    >>> print ("%2.4f" % (wikipedia_long_coil ( 33, 0.04, 0.64) * 1e6))
    2.6870
    >>> print ("%2.4f" % (wikipedia_long_coil (100, 0.02, 0.08) * 1e6))
    49.3480
    """
    return mu0 * n**2 * A (d) / l

def wikipedia_short_coil (n, d, l) :
    """ Short coil according to wikipedia
        https://de.wikipedia.org/wiki/Zylinderspule
    >>> print ("%2.4f" % (wikipedia_short_coil (33, 0.04, 0.0264) * 1e6))
    38.7315
    >>> print ("%2.4f" % (wikipedia_short_coil (30, 0.04, 0.0186) * 1e6))
    38.8312
    >>> print ("%2.4f" % (wikipedia_short_coil (44, 0.04, 0.0616) * 1e6))
    38.4071
    >>> print ("%2.4f" % (wikipedia_short_coil (80, 0.04, 0.2400) * 1e6))
    39.1724
    >>> print ("%2.4f" % (wikipedia_short_coil (10, 2,    0.008)  * 1e6))
    434.7843
    """
    return mu0 * n**2 * A (d) / (l + 0.9 * d / 2.0)

if __name__ == "__main__" :
    import sys
    if len (sys.argv) != 5 :
        print \
            ( "Usage: %s diameter windings wirediameter pitch" % sys.argv [0]
            , file = sys.stderr \
            )
        sys.exit (23)
    args = [float (i) for i in sys.argv [1:]]
    print (induction (*args [:3], pitch = args [3]))
