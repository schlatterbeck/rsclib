#!/usr/bin/python3
# Copyright (C) 2013-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
