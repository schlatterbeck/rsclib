#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2007 Dr. Ralf Schlatterbeck Open Source Consulting.
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

def extended_euclid (m, n) :
    """ Extended Euclids Algorithm from Knuth, The Art of Computer
        Programming Vol. 1, Fundamental Algorithms, Algorithm "E" p. 14.
        This function returns d, a, b, where d is the gcd of m and n and
        a, b are the multiplicative inverses of m mod n and n mod m,
        respectively, if m and n are relative prime.
        See Exercise 19, p. 40 -- the proof is simple, if m and n are
        relative prime then the invariant A4 in Fig. 4 p. 15:
        am + bn = d
        becomes
        am + bn = 1
        take this mod m:
        bn = 1
        or mod n:
        am = 1
        which is the definition of the multiplicative inverse.
        >>> extended_euclid (1769, 551)
        (29, 5, 1753)
        >>> extended_euclid (40, 23)
        (1, 19, 7)
    """
    a_o = b = 1
    b_o = a = 0
    c = m
    d = n
    while 1 :
        q, r = divmod (c, d)
        if r == 0 :
            return d, a % n, b % m
        c   = d
        d   = r
        t   = a_o
        a_o = a
        a   = t - q * a
        t   = b_o
        b_o = b
        b   = t - q * b
# end def extended_euclid

def gcd (m, n) :
    """ Greatest common divisor implemented by Euclids algorithm.
        >>> gcd (23, 17)
        1
        >>> gcd (23, 46)
        23
        >>> gcd (1769, 551)
        29
    """
    return extended_euclid (m, n) [0]
# end def gcd

def lcm (m, n) :
    """ Least Common Multiple
        >>> lcm (23, 17)
        391
        >>> lcm (23, 46)
        46
        >>> lcm (1769, 551)
        33611
    """
    return m * (n // gcd (m, n))
# end def lcm

def binom (n, m) :
    """ Compute binomial coefficient of n, m """
    b = [0] * (n + 1)
    b [0] = 1
    for i in range (1, n + 1) :
        b [i] = 1
        j = i - 1
        while j > 0 :
            b [j] += b [j - 1]
            j -= 1
    return b [m]
# end def binom
