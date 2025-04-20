#!/usr/bin/python3
# Copyright (C) 2005-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__ import division
from rsclib.pycompat  import long_type
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
        >>> a = PM_Value (1)
        >>> b = PM_Value (2)
        >>> a // b
        0
        >>> a / b
        0.5
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

    def __eq__ (self, other) :
        return self.value == getattr (other, 'value', other)
    # end def __eq__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __nonzero__ (self) :
        return bool (self.value)
    # end def __nonzero__
    __bool__ = __nonzero__

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
    ( '__add__',      '__sub__', '__mul__', '__truediv__'
    , '__floordiv__', '__mod__', '__pow__', '__lshift__', '__rshift__'
    , '__and__',      '__xor__', '__or__'
    ) :
    _define_binop (name)

for name in ('__neg__', '__pos__', '__abs__', '__invert__') :
    _define_unop (name)

for func in (int, long_type, float, str, repr) :
    _define_convop (func)

del name, func

