#!/usr/bin/python
# Copyright (C) 2011-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
import sys
from rsclib.pycompat import bytes_ord, PY2

def ascii (s) :
    if not PY2 :
        if s > 128 :
            return '.'
        s = chr (s)
    if len (repr (s)) > 3 :
        return '.'
    return s
# end def ascii

def hexdump (s, start = 0, show_addr = True, last_addr = True) :
    """
    >>> a = b'1234567890abcdefghijklmnopqrstuv'
    >>> print (hexdump (a + b'\\xce\\x02\\xb9\x49', show_addr = False))
    31 32 33 34 35 36 37 38 39 30 61 62 63 64 65 66   1234567890abcdef
    67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 76   ghijklmnopqrstuv
    ce 02 b9 49                                       ...I            
    >>> print (hexdump (a + b'\\xce\\x02\\xb9\x49'))
    00000000  31 32 33 34 35 36 37 38 39 30 61 62 63 64 65 66   1234567890abcdef
    00000010  67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 76   ghijklmnopqrstuv
    00000020  ce 02 b9 49                                       ...I            
    """
    assert isinstance (s, type (b''))
    r = []
    for x in range (len (s) // 16 + 1) :
        slc  = s [x*16:(x+1)*16]
        adr  = '%08x'  % (start + x * 16)
        hex  = '%-48s' % ' '.join \
            ("%02x" % bytes_ord (k) for k in slc)
        char = '%-16s' % ''.join (ascii (k) for k in slc)
        vars = (adr, hex, char)
        if not show_addr :
            vars = (hex, char)
        if last_addr or slc :
            r.append ('  '.join (vars))
    return '\n'.join (r)
# end def hexdump

def unhexdump (iterable, file = None) :
    """ Convert a hex-dump to binary
    """
    bin = []
    end = False
    for line in iterable :
        line = line.strip ()
        if not line :
            continue
        if end :
            raise ValueError ("Unknown hexdump format")
        x = line.split ('  ', 2)
        if len (x) == 1 :
            h = x [0]
        else :
            h = x [1]
            assert len (x [0]) <= 8
        # Probably last line with only an address
        if ' ' not in h and len (x) == 1 and len (h) > 2 :
            end = True
            continue
        h = h.strip ().split (' ')
        if len (h [0]) > 2 :
            h = h [1:]
        if sys.version_info [0] < 3 :
            method = lambda x : b''.join (chr (c) for c in x)
        else :
            method = bytes
        if file :
            file.write (method ((int (k, 16)) for k in h))
        else :
            bin.append (method ((int (k, 16)) for k in h))
    if file :
        file.flush ()
        return None
    return b''.join (bin)
# end def unhexdump
