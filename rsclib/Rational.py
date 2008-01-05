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

from rsclib.autosuper import autosuper
from rsclib.Math      import gcd, lcm

class Rational (autosuper) :
    """ Rational number implemented as quotient of two (long) integers
        >>> R = Rational
        >>> R (21, 6) - R (7, 6)
        7/3 = 2 1/3
        >>> R (21, 6) + R (7, 6)
        14/3 = 4 2/3
        >>> R (21, 6) * R (6, 7)
        3
        >>> R (21, 6) / R (7, 6)
        3
        >>> R (1, 8) * R (4)
        1/2
        >>> R (1, 8) * 4
        1/2
        >>> R (0, 4711) * 10
        0
        >>> R (1,2) / R (0)
        Traceback (most recent call last):
            ...
        ZeroDivisionError: integer division by zero
        >>> R (1,0)
        Traceback (most recent call last):
            ...
        ZeroDivisionError: integer division by zero
        >>> R (12) == R (12, 1)
        True
        >>> R (3, 4) < R (5, 4)
        True
        >>> R (3, 4) >= R (5, 4)
        False
        >>> 2 + R (3, 4)
        11/4 = 2 3/4
        >>> 2 - R (3, 4)
        5/4 = 1 1/4
        >>> 2 * R (3, 4)
        3/2 = 1 1/2
        >>> 2 / R (3, 4)
        8/3 = 2 2/3
        >>> int (R (3, 4))
        0
        >>> int (R (4, 3))
        1
        >>> long (R (3, 4))
        0L
        >>> long (R (4, 3))
        1L
        >>> bool (R (3, 4))
        True
        >>> bool (R (0, 2))
        False
    """
    def __init__ (self, p, q = 1) :
        if isinstance (p, Rational) :
            p /= q
            self.p = p.p, self.q = p.q
        elif isinstance (p, int) or isinstance (p, long) :
            self.p = p
        else :
            raise ValueError ("Unsupported operand type: %s" % type (p))
        if q == 0 :
            raise ZeroDivisionError ("integer division by zero")
        if self.p == 0 :
            self.q = 1
        elif isinstance (q, int) or isinstance (q, long) :
            if q < 0 :
                self.p = - self.p
            self.q  = abs (q)
            k       = gcd (abs (self.p), q)
            self.p  = self.p / k
            self.q  = self.q / k
        else :
            x = self / q
            self.p = x.p
            self.q = x.q
    # end def __init__

    def __add__ (self, other) :
        if not isinstance (other, self.__class__) :
            other = self.__class__ (other)
        q = lcm (self.q, other.q)
        p = self.p * q / self.q + other.p * q / other.q
        return self.__class__ (p, q)
    # end def __add__ (self, other)

    def __cmp__ (self, other) :
        return (self - other).p
    # end def __cmp__

    def __div__ (self, other) :
        if not isinstance (other, self.__class__) :
            other = self.__class__ (other)
        p = self.p * other.q
        q = self.q * other.p
        return self.__class__ (p, q)
    # end def __div__

    def __int__ (self) :
        return int (self.p / self.q)
    # end def __int__

    def __long__ (self) :
        return long (self.p / self.q)
    # end def __long__

    def __mul__ (self, other) :
        if not isinstance (other, self.__class__) :
            other = self.__class__ (other)
        p = self.p * other.p
        q = self.q * other.q
        return self.__class__ (p, q)
    # end def __mul__

    def __neg__ (self) :
        return self.__class__ (-self.p, self.q)
    # end def __neg__

    def __nonzero__ (self) :
        return bool (self.p)
    # end def __nonzero__

    def __radd__ (self, other) :
        return self + other
    # end def __radd__

    def __rdiv__ (self, other) :
        return self.__class__ (other) / self
    # end def __rdiv__

    def __repr__ (self) :
        if self.q == 1 :
            return "%d" % self.p
        g = ""
        if self.p > self.q :
            g = " = %d %d/" % divmod (self.p, self.q) + '%d' % self.q
        return "%d/%d%s" % (self.p, self.q, g)
    # end def __repr__

    def __rmul__ (self, other) :
        return self * other
    # end def __rmul__

    def __rsub__ (self, other) :
        return self.__class__ (other) - self
    # end def __rsub__

    __str__ = __repr__

    def __sub__ (self, other) :
        return self + -other
    # end def __sub__

# end class Rational
