#!/usr/bin/python3
# Copyright (C) 2013-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
#
# Python compatibility. Some code taken from Armin Ronacher's excellent
# blog article on python2 vs. python3 porting, see
#

from __future__ import absolute_import
from __future__ import print_function
import io
import sys

PY2 = sys.version_info [0] == 2
if PY2 :
    text_type    = unicode
    string_types = (str, unicode)
    unichr       = unichr
    long_type    = long
else :
    text_type    = str
    string_types = (str,)
    unichr       = chr
    long_type    = int

if PY2 :
    class ustr (unicode) :
        def __repr__ (self) :
            return unicode.__repr__ (self).lstrip ('u')
        # end def __repr__
    # end class ustr
    def longpr (* longvar) :
        """ For regression-testing """
        for l in longvar [:-1] :
            print (repr (l), end = ' ')
        print (repr (longvar [-1]))
    # end def longpr
else :
    ustr = text_type
    def longpr (* longvar) :
        """ For regression-testing """
        for l in longvar  [:-1]:
            print (str (l) + 'L', end = ' ')
        print (str (longvar [-1]) + 'L')
    # end def longpr

def with_metaclass (meta, *bases) :
    class metaclass (meta) :
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__ (cls, name, this_bases, d) :
            if this_bases is None :
                return type.__new__ (cls, name, (), d)
            return meta (name, bases, d)
    return metaclass ('temporary_class', None, {})
# end def with_metaclass

def assert_raises (exception, substr, function, * args) :
    try :
        function (* args)
    except exception as cause :
        if substr :
            if substr in str (cause) :
                return
            assert False
    assert False
# end def assert_raises

if PY2 :
    bytes_ord = ord
    tobytes   = chr
else :
    bytes_ord = lambda x : x if isinstance (x, int) else ord (x)
    tobytes   = lambda x : bytes ([x])

if PY2 :
    StringIO = io.BytesIO
else :
    StringIO = io.StringIO
