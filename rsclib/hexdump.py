#!/usr/bin/python
# Copyright (C) 2011-19 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import sys

def ascii (s) :
    if len (repr (s)) > 3 :
        return '.'
    return s
# end def ascii

def hexdump (s, start = 0, show_addr = True) :
    r = []
    for x in range (len (s) / 16 + 1) :
        adr  = '%08x'  % (start + x * 16)
        hex  = '%-48s' % ' '.join ("%02x" % ord (k) for k in s [x*16:(x+1)*16])
        char = '%-16s' % ''.join (ascii (k) for k in s [x*16:(x+1)*16])
        vars = (adr, hex, char)
        if not show_addr :
            vars = (hex, char)
        r.append ('  '.join (vars))
    return '\n'.join (r)
# end def hexdump

def unhexdump (iterable) :
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
        if len (x) <= 2 :
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
        bin.append (method ((int (k, 16)) for k in h))
    return b''.join (bin)
# end def unhexdump
