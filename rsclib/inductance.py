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
from math import pi, log, sqrt, e

mu0 = 4e-7 * pi

def A (d) :
    """ Area from diameter d
    >>> print ("%2.2f" % A (10))
    78.54
    """
    return pi * (d/2.0) ** 2

def L_s (l, d, n) :
    """ Inductance in H for an air-cored cylindrical flat-winded coil
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

def nagaoka (u) :
    """ Nagaoka's coefficient computed with iterative elliptic integral
        method, see http://electronbunker.ca/eb/CalcMethods1a.html
        we use the iterated elliptic integral calculation
        e.g., the Javascript implementation there.
    >>> nagaoka (0)
    1.0
    >>> print ("%2.5f" % nagaoka (0.01))
    0.99577
    >>> print ("%2.5f" % nagaoka (0.02))
    0.99156
    >>> print ("%2.5f" % nagaoka (0.03))
    0.98738
    >>> print ("%2.5f" % nagaoka (0.04))
    0.98322
    >>> print ("%2.5f" % nagaoka (0.05))
    0.97909
    >>> print ("%2.5f" % nagaoka (0.10))
    0.95881
    >>> print ("%2.5f" % nagaoka (0.15))
    0.93914
    >>> print ("%2.5f" % nagaoka (0.20))
    0.92009
    >>> print ("%2.5f" % nagaoka (0.25))
    0.90165
    >>> print ("%2.5f" % nagaoka (0.30))
    0.88380
    >>> print ("%2.5f" % nagaoka (0.35))
    0.86654
    >>> print ("%2.5f" % nagaoka (0.40))
    0.84985
    >>> print ("%2.5f" % nagaoka (0.45))
    0.83372
    >>> print ("%2.5f" % nagaoka (0.50))
    0.81814
    >>> print ("%2.5f" % nagaoka (0.55))
    0.80308
    >>> print ("%2.6f" % nagaoka (0.60))
    0.788525
    >>> print ("%2.5f" % nagaoka (0.65))
    0.77447
    >>> print ("%2.5f" % nagaoka (0.70))
    0.76089
    >>> print ("%2.5f" % nagaoka (0.75))
    0.74776
    >>> print ("%2.5f" % nagaoka (0.80))
    0.73508
    >>> print ("%2.5f" % nagaoka (0.85))
    0.72282
    >>> print ("%2.5f" % nagaoka (0.90))
    0.71097
    >>> print ("%2.5f" % nagaoka (0.95))
    0.69951
    >>> print ("%2.5f" % nagaoka (1.0))
    0.68842
    >>> print ("%2.5f" % nagaoka (1.5))
    0.59505
    >>> print ("%2.5f" % nagaoka (2.0))
    0.52551
    >>> print ("%2.5f" % nagaoka (3.0))
    0.42920

    # This disagrees with nagaoka, he has .365438
    >>> print ("%2.6f" % nagaoka (4.0))
    0.365432
    >>> print ("%2.5f" % nagaoka (5.0))
    0.31983
    >>> print ("%2.5f" % nagaoka (6.0))
    0.28541
    >>> print ("%2.5f" % nagaoka (7.0))
    0.25841
    >>> print ("%2.5f" % nagaoka (8.0))
    0.23658
    >>> print ("%2.5f" % nagaoka (9.0))
    0.21853
    >>> print ("%2.5f" % nagaoka (10.0))
    0.20332
    """
    if u == 0 :
        return 1.0
    uu = u ** 2
    m  = uu / (1.0 + uu)
    m2 = 4 * sqrt (1 + uu)
    a  = 1
    b  = sqrt (1 - m)
    c  = a - b
    ci = 1
    cs = (c ** 2 / 2) + m
    co = 1e12 # loop at least once
    while c < co :
        an = (a + b) / 2
        b  = sqrt (a * b)
        a  = an
        co = c
        c  = a - b
        cs += ci * c ** 2
        ci *= 2
    cs /= 2.0
    K   = pi / (2 * a)
    KmE = K * cs
    E   = K * (1 - cs)
    return 1 / (3 * pi) * (m2 / uu * KmE + m2 * E - 4 * u)
# end def nagaoka

def L_s_Lorenz (l, d, n) :
    """ Current-Sheet inductance according to Lorenz corrected for SI
        units, see http://electronbunker.ca/eb/CalcMethods1a.html
    """
    u = l / d
    r = d / 2.0
    return (mu0 * pi * n ** 2 * r ** 2 / l) * nagaoka (u)
# end def L_s_Lorenz

# in nano-Ohm * meter (SI would be Ohm * mm^2 / m, we have factor 10^3)
# Values from http://www.g3ynh.info/zdocs/comps/part_1.html
# German Wikipedia has some different values:
# al = 26.5
# au = 22.14
# cu = 17.21 ("rein")
# cu = 16.9 -- 17.5 ("Elektro-Kabel")
# sn = 109
# It agrees for pt, ag
# But looking up the conductivity again yields different values.
rho_m = dict \
    ( al  =  28.24
    , cuh =  17.71  # hard drawn
    , cu  =  17.241 # annealed
    , au  =  24.4
    , pt  = 105.0
    , ag  =  15.87
    , sn  = 115.0
    , zn  =  58.0
    , ni  =  78.0
    , fe  = 100.0
    )

mu_r = dict \
    ( fe = 200
    , ni = 250
    )

def L_e (d, d_w) :
    """ External inductance of a single-turn loop according to
        http://www.g3ynh.info/zdocs/comps/part_2.html (6.2) and previous
        unnumbered equation.
    >>> print ("%3.2f" % (L_e (0.06366, 0.00163) * 1e9))
    149.77
    """
    r = d / 2.0
    return mu0 * r * (log (8 * d / d_w) - 2)
# end def L_e

def delta_i (f, rho = rho_m ['cu'], mur = 1) :
    """ Skin depth at given frequency, rho defaults to copper
        http://www.g3ynh.info/zdocs/comps/part_1.html (2.2)
        Frequency f in Hz, delta_i in m
        mur = µr in nano-ohm-meter
    >>> print ("%3.1f" % (delta_i (136e3)  * 1e6))
    179.2
    >>> print ("%3.1f" % (delta_i (1.9e6)  * 1e6))
    47.9
    >>> print ("%3.1f" % (delta_i (3.7e6)  * 1e6))
    34.4
    >>> print ("%3.1f" % (delta_i (7.1e6)  * 1e6))
    24.8
    >>> print ("%3.1f" % (delta_i (10.1e6) * 1e6))
    20.8
    >>> print ("%3.1f" % (delta_i (14.2e6) * 1e6))
    17.5
    >>> print ("%3.1f" % (delta_i (18.1e6) * 1e6))
    15.5
    >>> print ("%3.1f" % (delta_i (21.3e6) * 1e6))
    14.3
    >>> print ("%3.1f" % (delta_i (24.9e6) * 1e6))
    13.2
    >>> print ("%3.1f" % (delta_i (29e6)   * 1e6))
    12.3
    >>> print ("%3.1f" % (delta_i (51e6)   * 1e6))
    9.3
    >>> print ("%3.1f" % (delta_i (145e6)  * 1e6))
    5.5
    >>> rfe = rho_m  ['fe']
    >>> mfe = mu_r  ['fe']
    >>> print ("%3.1f" % (delta_i (136e3, rho = rfe, mur = mfe)  * 1e6))
    30.5
    >>> print ("%3.1f" % (delta_i (1.9e6, rho = rfe, mur = mfe)  * 1e6))
    8.2
    >>> print ("%3.1f" % (delta_i (3.7e6, rho = rfe, mur = mfe)  * 1e6))
    5.9
    >>> print ("%3.1f" % (delta_i (7.1e6, rho = rfe, mur = mfe)  * 1e6))
    4.2
    >>> print ("%3.1f" % (delta_i (10.1e6, rho = rfe, mur = mfe) * 1e6))
    3.5
    >>> print ("%3.1f" % (delta_i (14.2e6, rho = rfe, mur = mfe) * 1e6))
    3.0
    >>> print ("%3.1f" % (delta_i (18.1e6, rho = rfe, mur = mfe) * 1e6))
    2.6
    >>> print ("%3.1f" % (delta_i (21.3e6, rho = rfe, mur = mfe) * 1e6))
    2.4
    >>> print ("%3.1f" % (delta_i (24.9e6, rho = rfe, mur = mfe) * 1e6))
    2.3
    >>> print ("%3.1f" % (delta_i (29e6, rho = rfe, mur = mfe)   * 1e6))
    2.1
    >>> print ("%3.1f" % (delta_i (51e6, rho = rfe, mur = mfe)   * 1e6))
    1.6
    >>> print ("%3.1f" % (delta_i (145e6, rho = rfe, mur = mfe)  * 1e6))
    0.9
    """
    return 1.0 / sqrt (mu0 * mur * pi * f / (rho * 1e-9))
# end def delta_i

def L_i (f, d, d_w, material = 'cu') :
    """ Internal inductance of a single-turn loop (or a straight wire)
        according to http://www.g3ynh.info/zdocs/comps/part_2.html (6.1)
    >>> print ("%3.2f" % (L_i (5e6, 0.06366, 0.00163) * 1e9))
    0.73
    """
    l   = d * pi
    mur = mu_r.get (material, 1.0)
    rho = rho_m [material]
    return l * (mu0 * mur / (2.0 * pi)) * delta_i (f, rho, mur) / d_w
# end def L_i

def flpml (q) :
    """ Internal inductance factor D. W. Knight
        http://www.g3ynh.info/zdocs/comps/Zint.pdf
    """
    if q < 0.0001 :
        return 1.0
    f  = \
       ( (4.0 / q)
       * (1.0 / sqrt (2))
       * ( 1.0
         + 0.01209 / (q + 1.0)
         - 0.63523 / (q ** 2 + 1)
         + 0.16476 / (q ** 3 + 1)
         )
       )
    f  = f * (1.0 - e ** (-1.0 * f ** -1.5819)) ** 0.63215121
    z  = 0.38691 * q
    zz = z ** 1.2652 - z ** -0.39709
    y  = -0.198584 / ((1.0 + 0.25741 * zz ** 2) ** 2.62343)
    f  = f * (1.0 - y)
    return f
# end def flpml

def L_i_PACAML (f, lw, d_w, material = 'cu') :
    """ Internal Inductance to withing 151 ppM D. W. Knight
        http://www.g3ynh.info/zdocs/comps/Zint.pdf
        lw is the wire length.
    """
    rho = rho_m [material]
    mur = mu_r.get (material, 1.0)
    d   = delta_i (f, rho, mur)
    q   = d_w / (d * sqrt (2))
    return lw * 0.5e-7 * mur * flpml (q)
# end def L_i_PACAML

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
    return mu0 * r * n * (k_s (pitch, d_w) + k_m (n))
# end def delta_roundwire

def induction (d, n, d_w, l = 0, pitch = 0, f = 0, material = 'cu') :
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
        Note that for a single turn we use the formula from
        http://www.g3ynh.info/zdocs/comps/part_2.html with optional
        internal inductance (if frequency is given).
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

    # Single Turn, special handling
    >>> print ("%3.2f" % (induction (5, 1, 0.0235, 0.0235, f=1.9e6)*1e6))
    17.10
    
    # From http://www.g3ynh.info/zdocs/comps/part_2.html
    >>> print ("%3.2f" % (induction (0.06366, 1, 0.00163, 0.00163, f=5e6)*1e9))
    150.50
    >>> print ("%3.2f" % (induction (0.06366, 1, 0.000376, 0.00163, f=5e6)*1e9))
    211.58
    >>> print ("%3.2f" % (induction (0.06366, 1, 0.000193, 0.00163, f=5e6)*1e9))
    241.24
    """
    if l :
        pitch = float (l) / float (n)
    elif pitch :
        l = float (pitch) * float (n)
    else :
        raise ValueError ("l or pitch must be != 0")
    if n == 1 :
        v = L_e (d, d_w)
        if f :
            v += L_i (f, d, d_w, material)
        return v
    v = L_s (l, d, n) - delta_roundwire (d / 2.0, n, pitch, d_w)
    # FIXME: Frequency correction
    return v
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
