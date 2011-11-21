#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

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
        http://electronbunker.sasktelwebsite.net/CalcMethods3b.html
        where he used a solver to optimize the formula for low errors.
        Note: This is a current sheet formula, and will require round
        wire corrections for best accuracy.
    >>> print "%2.5f" % L_s ( 0.8,   2,  10)
    2.32856
    >>> print "%2.5f" % L_s ( 1.6,   2,  20)
    6.29773
    >>> print "%2.5f" % L_s ( 4.0,   2,  50)
    20.18669
    >>> print "%2.5f" % L_s ( 8.0,   2, 100)
    44.49461
    >>> print "%2.5f" % L_s ( 2.0,   2,  10)
    1.35889
    >>> print "%2.5f" % L_s ( 4.0,   2,  20)
    3.22987
    >>> print "%2.5f" % L_s (10.0,   2,  50)
    9.08095
    >>> print "%2.5f" % L_s (20.0,   2, 100)
    18.92609
    >>> print "%2.5f" % L_s ( 0.8,  10,   10)
    21.45928
    >>> print "%2.5f" % L_s ( 8.0,  10,  100)
    787.21645
    >>> print "%2.5f" % L_s ( 0.8, 200,   10)
    805.22408
    >>> print "%2.5f" % L_s ( 8.0, 200,  100)
    51599.29039
    """
    u = float (l) / float (d)
    return 0.002 * pi * d * n**2 * \
        ( log (1.0 + (pi * d) / (2.0 * l))
        + 1.0
          / ( (1. / (log (8. / pi) - 0.5))
            + 3.437  * u
            + (24. / (3. * pi**2 - 16)) * (u ** 2)
            - 0.47 * ((0.755 + u) ** 1.44)
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
        http://electronbunker.sasktelwebsite.net/CalcMethods2a.html
        n is the number of turns, r is the coil radius.
        The winding pitch and conductor diameter are in cm.
    >>> print "%2.5f" % delta_roundwire (1,  10, 0.080, 0.05)
    0.04439
    >>> print "%2.5f" % delta_roundwire (1,  20, 0.080, 0.05)
    0.09631
    >>> print "%2.5f" % delta_roundwire (1,  50, 0.080, 0.05)
    0.25451
    >>> print "%2.5f" % delta_roundwire (1, 100, 0.080, 0.05)
    0.51992
    >>> print "%2.5f" % delta_roundwire (1,  10, 0.200, 0.05)
    -0.07075
    >>> print "%2.5f" % delta_roundwire (1,  20, 0.200, 0.05)
    -0.13398
    >>> print "%2.5f" % delta_roundwire (1,  50, 0.200, 0.05)
    -0.32121
    >>> print "%2.5f" % delta_roundwire (1, 100, 0.200, 0.05)
    -0.63152
    >>> print "%2.5f" % delta_roundwire (  5,  10, 0.080, 0.05)
    0.22196
    >>> print "%2.5f" % delta_roundwire (  5, 100, 0.080, 0.05)
    2.59962
    >>> print "%2.5f" % delta_roundwire (100,  10, 0.080, 0.05)
    4.43916
    >>> print "%2.5f" % delta_roundwire (100, 100, 0.080, 0.05)
    51.99242
    """
    return 0.004 * pi * r * n * (k_s (pitch, diameter) + k_m (n))
# end def delta_roundwire

def induction (l, d, n, diameter) :
    """ induction with round-wire correction
    >>> print "%2.5f" % induction ( 0.8,   2,  10, 0.05)
    2.28417
    >>> print "%2.5f" % induction ( 1.6,   2,  20, 0.05)
    6.20142
    >>> print "%2.5f" % induction ( 4.0,   2,  50, 0.05)
    19.93218
    >>> print "%2.5f" % induction ( 8.0,   2, 100, 0.05)
    43.97469
    >>> print "%2.5f" % induction ( 2.0,   2,  10, 0.05)
    1.42964
    >>> print "%2.5f" % induction ( 4.0,   2,  20, 0.05)
    3.36385
    >>> print "%2.5f" % induction (10.0,   2,  50, 0.05)
    9.40216
    >>> print "%2.5f" % induction (20.0,   2, 100, 0.05)
    19.55761
    >>> print "%2.5f" % induction ( 0.8,  10,  10, 0.05)
    21.23732
    >>> print "%2.5f" % induction ( 8.0,  10, 100, 0.05)
    784.61683
    >>> print "%2.5f" % induction ( 0.8, 200,  10, 0.05)
    800.78491
    >>> print "%2.5f" % induction ( 8.0, 200, 100, 0.05)
    51547.29797
    """
    pitch = float (l) / float (n)
    return L_s (l, d, n) - delta_roundwire (d / 2.0, n, pitch, diameter)
# end def induction
