#!/usr/bin/python
# Copyright (C) 2005 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import operator
from rsclib.autosuper import autosuper

class PM_Value (autosuper) :
    """
        Possibly missing value: encapsulates a number and the
        information how many missing values have been used in the
        computation of value.
        >>> a = b = PM_Value (None)
        >>> a == 0
        True
        >>> not a
        True
        >>> a.missing
        1
        >>> a + b
        0
        >>> (a + b).missing
        2
        >>> (a * b).missing
        2
        >>> a += 1
        >>> a
        1
        >>> not a
        False
        >>> a == 1
        True
        >>> b
        0
        >>> a.missing
        1
        >>> a += a
        >>> a
        2
        >>> a.missing
        2
        >>> a += 0.0
        >>> a
        2.0
        >>> a.missing
        2
        >>> a += 1j
        >>> a
        (2+1j)
        >>> a.missing
        2
        >>> a + 2
        (4+1j)
        >>> a + a
        (4+2j)
        >>> a += a
        >>> a
        (4+2j)
        >>> a.missing
        4
        >>> b
        0
        >>> b.missing
        1
    """

    def __init__ (self, value = None, missing = 0) :
        if isinstance (value, PM_Value) :
            missing = value.missing
            value   = value.value
        self.missing = missing
        self.value   = value or 0
        if value is None :
            self.missing += 1
    # end def __init__

    def __cmp__ (self, other) :
        return cmp (self.value, getattr (other, 'value', other))
    # end def __cmp__

    def __nonzero__ (self) :
        return bool (self.value)
    # end def __nonzero__

# end class PM_Value

def _set_method (name, fct) :
    fct.__doc__ = getattr (int, name).__doc__
    try :
        fct.__name__ = name
    except TypeError :
        pass
    setattr (PM_Value, name, fct)
# end def _set_method

def _define_binop (name) :
    op = getattr (operator, name)
    def _ (self, r) :
        return PM_Value \
            ( op (self.value, getattr (r, 'value', r))
            , self.missing + getattr (r, 'missing', 0)
            )
    _set_method (name, _)
# end _define_binop

def _define_unop (name) :
    op = getattr (operator, name)
    def _ (self) :
        return PM_Value (op (self.value), self.missing)
    _set_method (name, _)
# end _define_unop

def _define_convop (func) :
    name = '__%s__' % func.__name__
    def _ (self) :
        return func (self.value)
    _set_method (name, _)
# end _define_convop

for name in \
    ( '__add__',      '__sub__', '__mul__', '__div__',    '__truediv__'
    , '__floordiv__', '__mod__', '__pow__', '__lshift__', '__rshift__'
    , '__and__',      '__xor__', '__or__'
    ) :
    _define_binop (name)

for name in ('__neg__', '__pos__', '__abs__', '__invert__') :
    _define_unop (name)

for func in (int, long, float, oct, hex, str, repr) :
    _define_convop (func)

del name, func

