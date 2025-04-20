#!/usr/bin/python
# Copyright (C) 2007 Dr. Ralf Schlatterbeck Open Source Consulting.
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
