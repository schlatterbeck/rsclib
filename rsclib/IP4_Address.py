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


class IP4_Address :
    """
        IP version 4 Address with optional subnet mask.
        >>> a = IP4_Address ('10.100.10.0')
        >>> a.ip
        174328320L
        >>> str (a)
        '10.100.10.0'
        >>> b = IP4_Address ('10.100.10.5', 24)
        >>> b.ip
        174328320L
        >>> str (b)
        '10.100.10.0/24'
        >>> b.subnet_mask ()
        255.255.255.0
        >>> b.broadcast_address ()
        10.100.10.255
        >>> b
        10.100.10.0/24
        >>> b in b
        True
        >>> c = IP4_Address ('10.100.10.5', 16)
        >>> b in c
        True
        >>> c in b
        False
        >>> c.ip
        174325760L
        >>> str (c)
        '10.100.0.0/16'
        >>> d = IP4_Address ('10.100.0.0/24', 16)
        >>> d.ip
        174325760L
        >>> str (d)
        '10.100.0.0/16'
        >>> str (d.subnet_mask ())
        '255.255.0.0'
        >>> print d.subnet_mask ()
        255.255.0.0
        >>> d.broadcast_address ()
        10.100.255.255
        >>> d.net ()
        10.100.0.0
        >>> e = IP4_Address ('10.100.0.0')
        >>> e.ip
        174325760L
        >>> str (e)
        '10.100.0.0'
        >>> str (IP4_Address (174325760L))
        '10.100.0.0'
        >>> str (IP4_Address (65535))
        '0.0.255.255'
        >>> IP4_Address (0xFFFFFFFF)
        255.255.255.255
        >>> adr = IP4_Address ('10.100.10.1')
        >>> adr in IP4_Address ('10.100.0.0', 16)
        True
        >>> adr in IP4_Address ('10.100.10.0', 24)
        True
        >>> adr in IP4_Address ('10.100.20.0', 16)
        True
        >>> adr in IP4_Address ('10.100.20.0', 24)
        False
        >>> adr.contains (IP4_Address ('10.100.20.0', 24))
        False
        >>> f = IP4_Address ('10.100.10.1', 24)
        >>> f.overlaps (f)
        True
        >>> f.overlaps (IP4_Address (f.ip, 16))
        True
        >>> f = IP4_Address (f.ip, 16)
        >>> f
        10.100.0.0/16
        >>> f.overlaps (f)
        True
        >>> g = IP4_Address ('10.100.10.2', 32)
        >>> f.overlaps (g)
        True
        >>> g.overlaps (g)
        True
        >>> g.overlaps (IP4_Address ('10.101.10.2', 32))
        False
        >>> g.overlaps (IP4_Address ('10.100.10.3', 32))
        False
        >>> g.ip, g.bitmask
        (174328322L, 4294967295L)
        >>> g
        10.100.10.2
        >>> g == g
        True
        >>> g == f
        False
        >>> f
        10.100.0.0/16
        >>> f == IP4_Address ('10.100.0.0')
        False
        >>> f.contains (IP4_Address ('10.100.0.0'))
        True
        >>> f == IP4_Address ('10.100.0.0', 16)
        True
    """

    def __init__ (self, address, mask = 32L) :
        self.mask = long (mask)
        if isinstance (address, str) :
            self._from_string (address)
        else :
            self.ip = long (address)
        self.bitmask = ((1L << self.mask) - 1L) << (32L - self.mask)
        self.ip &= self.bitmask
    # end def __init__

    def broadcast_address (self) :
        mask = ~self.bitmask
        return self.__class__ (self.ip | mask)
    # end def broadcast_address

    def contains (self, other) :
        return other.mask >= self.mask and self.ip == (other.ip & self.bitmask)
    # end def contains

    def net (self) :
        return self.__class__ (self.ip & self.bitmask)
    # end def net

    def overlaps (self, other) :
        return \
            (  self.ip &  self.bitmask == other.ip &  self.bitmask
            or self.ip & other.bitmask == other.ip & other.bitmask
            )
    # end def overlaps

    def subnet_mask (self) :
        return self.__class__ (0xFFFFFFFF & self.bitmask)
    # end def subnet_mask

    __contains__ = contains

    def __eq__ (self, other) :
        return self.ip == other.ip and self.mask == other.mask
    # end def __eq__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __repr__ (self) :
        ip = self.ip
        r = []
        for i in range (4) :
            r.append (ip & 255)
            ip >>= 8
        ret = '.'.join (str (k) for k in reversed (r))
        if self.mask != 32 :
            ret += '/%s' % self.mask
        return ret
    # end def __repr__

    __str__ = __repr__

    def _from_string (self, address) :
        xadr = address.split ('/', 1)
        if len (xadr) > 1 :
            self.mask = min (self.mask, long (xadr [1]))
        n = 0L
        for octet in xadr [0].split ('.') :
            n <<= 8L
            n  |= long (octet)
        self.ip = n
    # end def _from_string

# end class IP4_Address

if __name__ == "__main__" :

    import sys

    def interfaces (ip, mask) :
        x = IP4_Address (ip, mask)
        print "address %s" % ip
        print "netmask %s" % x.subnet_mask ()
        print "network %s" % x.net ()
        print "broadcast %s" % x.broadcast_address ()
    # end def interfaces

    interfaces (sys.argv [1], int (sys.argv [2]))
