#!/usr/bin/python
# Copyright (C) 2005-12 Dr. Ralf Schlatterbeck Open Source Consulting.
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

mask_bits = \
    { 0 : 0, 128 : 1, 192 : 2, 224 : 3, 240 : 4, 248 : 5, 252 : 6, 254 : 7 }

def netmask_from_string (s) :
    """ Convert a netmask in dotted form to number of mask bits
    >>> netmask_from_string ('255.255.255.224')
    27
    >>> netmask_from_string ('0.0.0.0')
    0
    >>> netmask_from_string ('255.255.255.255')
    32
    >>> netmask_from_string ('255.255.254.0')
    23
    """
    mask = 0
    zero = False
    for n, octet in enumerate (s.split ('.'), 3) :
        v = int (octet)
        if zero :
            if v != 0 :
                raise ValueError, "Invalid Octet: %s in %s" % (octet, s)
        elif v == 255 :
            mask += 8
        elif v in mask_bits :
            mask += mask_bits [v]
            zero = True
        else :
            raise ValueError, "Invalid Octet: %s in %s" % (octet, s)
    return mask
# end def netmask_from_string

class IP_Address (autosuper) :

    bitlen = None

    def __init__ (self, address, mask = None) :
        if mask is None :
            mask = self.bitlen
        self.mask = long (mask)
        if self.mask < 0 or self.mask > self.bitlen :
            raise ValueError, "Invalid netmask: %s" % self.mask
        if isinstance (address, basestring) :
            xadr = address.split ('/', 1)
            if len (xadr) > 1 :
                m = long (xadr [1])
                if m < 0 or m > self.bitlen :
                    raise ValueError, "Invalid netmask: %s" % m
                self.mask = min (self.mask, m)
            self._from_string (xadr [0])
        else :
            self.ip = long (address)
        if self.ip >= (1L << self.bitlen) :
            raise ValueError, "Invalid ip: %s" % address
        self.bitmask = ((1L << self.mask) - 1L) << (self.bitlen - self.mask)
        self.invmask = (~self.bitmask) & ((1L << self.bitlen) - 1)
        self.ip &= self.bitmask
    # end def __init__

    def contains (self, other) :
        return other.mask >= self.mask and self.ip == (other.ip & self.bitmask)
    # end def contains

    @property
    def _broadcast (self) :
        return self.ip | self.invmask
    # end def _broadcast

    @property
    def broadcast_address (self) :
        return self.__class__ (self._broadcast)
    # end def broadcast_address

    broadcast = broadcast_address

    @property
    def net (self) :
        return self.__class__ (self.ip)
    # end def net
    
    network = net

    @property
    def netblk (self) :
        return [self.__class__ (x) for x in (self.ip, self._broadcast)]
    # end def netblk

    @property
    def subnet_mask (self) :
        return self.__class__ (self.bitmask)
    # end def subnet_mask

    netmask = subnet_mask

    def overlaps (self, other) :
        return \
            (  self.ip &  self.bitmask == other.ip &  self.bitmask
            or self.ip & other.bitmask == other.ip & other.bitmask
            )
    # end def overlaps

    def subnets (self, mask = None) :
        if mask is None :
            mask = self.bitlen
        inc = 1 << (self.bitlen - mask)
        if mask < self.mask :
            raise StopIteration
        # xrange doesn't support long ints :-(
        for i in xrange (0, self._broadcast - self.ip + 1, inc) :
            yield self.__class__ (i + self.ip, mask)
    # end def subnets

    def __cmp__ (self, other) :
        if not isinstance (other, self.__class__) :
            return cmp (type (self), type (other))
        return cmp (self.ip, other.ip) or cmp (other.mask, self.mask)
    # end def __cmp__

    __contains__ = contains

    def __eq__ (self, other) :
        if not isinstance (other, self.__class__) :
            return False
        return self.ip == other.ip and self.mask == other.mask
    # end def __eq__

    def __hash__ (self) :
        return str (self).__hash__ ()
    # end def __hash__

    __iter__ = subnets

    def __len__ (self) :
        return self._broadcast - self.ip + 1
    # end def __len__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __repr__ (self) :
        ret = self._to_str ()
        if self.mask != self.bitlen :
            ret += '/%s' % self.mask
        return ret
    # end def __repr__

    __str__  = __repr__

    # dangerous, put last to avoid conflict with built-in len
    # we keep this for compatibility with IPy
    len = __len__

# end def IP_Address

class IP4_Address (IP_Address) :
    """
        IP version 4 Address with optional subnet mask.
        >>> a = IP4_Address ('10.100.10.0')
        >>> a.ip
        174328320L
        >>> a._broadcast
        174328320L
        >>> str (a)
        '10.100.10.0'
        >>> a = IP4_Address (u'10.100.10.0')
        >>> str (a)
        '10.100.10.0'
        >>> aa = IP4_Address ('10.36.48.129', '255.255.255.224')
        >>> aa.mask
        27L
        >>> str (aa)
        '10.36.48.128/27'
        >>> b = IP4_Address ('10.100.10.5', 24)
        >>> b.ip
        174328320L
        >>> str (b)
        '10.100.10.0/24'
        >>> b.subnet_mask
        255.255.255.0
        >>> b.netmask
        255.255.255.0
        >>> b.broadcast_address
        10.100.10.255
        >>> b.broadcast
        10.100.10.255
        >>> b
        10.100.10.0/24
        >>> b = IP4_Address ('10.100.10.5/24')
        >>> b.ip
        174328320L
        >>> str (b)
        '10.100.10.0/24'
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
        >>> str (d.subnet_mask)
        '255.255.0.0'
        >>> print d.subnet_mask
        255.255.0.0
        >>> d.broadcast_address
        10.100.255.255
        >>> d.net
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
        >>> IP4_Address ('10.40.57.205').as_tc_basic_u32 ()
        'u32 (u32 0x0a2839cd 0xffffffff at 0xc)'
        >>> z = IP4_Address ('10.40.57.205/22')
        >>> z
        10.40.56.0/22
        >>> z.as_tc_basic_u32 (27)
        'u32 (u32 0x0a283800 0xfffffc00 at 0x10)'
        >>> list (sorted ((a, b, c, d, e, f, g)))
        [10.100.0.0, 10.100.0.0/16, 10.100.0.0/16, 10.100.0.0/16, 10.100.10.0, 10.100.10.0/24, 10.100.10.2]
        >>> IP4_Address ('108.62.8.0/21').netblk
        [108.62.8.0, 108.62.15.255]
        >>> i5 = IP4_Address ('10.23.5.0/30')
        >>> print "0x%X" % i5.bitmask
        0xFFFFFFFC
        >>> len (i5)
        4
        >>> i5.len ()
        4L
        >>> i5._broadcast
        169280771L
        >>> i5.netblk
        [10.23.5.0, 10.23.5.3]
        >>> for i in i5 :
        ...     print i
        10.23.5.0
        10.23.5.1
        10.23.5.2
        10.23.5.3
        >>> for i in i5.subnets () :
        ...     print i
        10.23.5.0
        10.23.5.1
        10.23.5.2
        10.23.5.3
        >>> for i in i5.subnets (24) :
        ...     print i
        >>> for i in i5.subnets (31) :
        ...     print i
        10.23.5.0/31
        10.23.5.2/31
        >>> i1 = IP4_Address ('10.23.5.5/24')
        >>> i2 = IP4_Address ('10.23.5.6/24')
        >>> d = dict.fromkeys ((i1, i2))
        >>> d
        {10.23.5.0/24: None}
        >>> IP4_Address ('1.2.3.4/33')
        Traceback (most recent call last):
         ...
        ValueError: Invalid netmask: 33
        >>> IP4_Address ('256.2.3.4')
        Traceback (most recent call last):
         ...
        ValueError: Invalid octet: 256
        >>> IP4_Address ('1.2.3.4.5')
        Traceback (most recent call last):
         ...
        ValueError: Too many octets: 1.2.3.4.5
    """

    bitlen = 32L

    def __init__ (self, address, mask = bitlen) :
        if isinstance (mask, basestring) and len (mask) > 3 :
            mask = netmask_from_string (mask)
        self.__super.__init__ (address, mask)
    # end def __init__

    def as_tc_basic_u32 (self, is_dst = False) :
        """ Compute tc "basic" u32 match.
            is_dst specifies a destination address, otherwise source is
            assumed.
        """
        return \
            ( "u32 (u32 0x%08x 0x%08x at 0x%x)"
            % (self.ip, self.bitmask, 12 + bool (is_dst) * 4)
            )
    # end def as_tc_basic_u32

    def dotted (self) :
        ip = self.ip
        r = []
        for i in range (4) :
            r.append (ip & 255)
            ip >>= 8
        return '.'.join (str (k) for k in reversed (r))
    # end def dotted
    _to_str = dotted

    def _from_string (self, address) :
        a = 0L
        for n, octet in enumerate (address.split ('.')) :
            a <<= 8L
            v = long (octet)
            if not (0 <= v <= 255) :
                raise ValueError, "Invalid octet: %s" % octet
            a |= long (octet)
            if n > 3 :
                raise ValueError, "Too many octets: %s" % address
        self.ip = a
    # end def _from_string

# end class IP4_Address

class IP6_Address (IP_Address) :
    """
        IP version 6 Address with optional subnet mask.
        >>> a = IP6_Address ("::")
        >>> a.ip
        0L
        >>> a._broadcast
        0L
        >>> a = IP6_Address ("::1")
        >>> a.ip
        1L
        >>> a = IP6_Address ("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        >>> print "%X" % a.ip
        20010DB885A3000000008A2E03707334
        >>> print "%X" % IP6_Address ("2001:db8:85a3:0:0:8a2e:370:7334").ip
        20010DB885A3000000008A2E03707334
        >>> print "%X" % IP6_Address ("2001:db8:85a3::8a2e:370:7334").ip
        20010DB885A3000000008A2E03707334
        >>> print "%X" % IP6_Address ("2001:db8:85a3::").ip
        20010DB885A300000000000000000000
        >>> print "%X" % IP6_Address ("::8a2e:370:7334").ip
        8A2E03707334
        >>> str (a)
        '2001:db8:85a3::8a2e:370:7334'
        >>> b = IP6_Address ('2001:db8:85a3::8a2e:370:7334', 64)
        >>> print "%X" % b.ip
        20010DB885A300000000000000000000
        >>> str (IP6_Address (0x20010DB885A300000000000000000000L))
        '2001:db8:85a3::'
        >>> str (b)
        '2001:db8:85a3::/64'
        >>> b.subnet_mask
        ffff:ffff:ffff:ffff::
        >>> b.netmask
        ffff:ffff:ffff:ffff::
        >>> b.broadcast_address
        2001:db8:85a3::ffff:ffff:ffff:ffff
        >>> b.broadcast
        2001:db8:85a3::ffff:ffff:ffff:ffff
        >>> b
        2001:db8:85a3::/64
        >>> b.net
        2001:db8:85a3::
        >>> b in b
        True
        >>> c = IP6_Address ('2001:db8:85a3::', 48)
        >>> b in c
        True
        >>> c in b
        False
        >>> print "%X" % c.ip
        20010DB885A300000000000000000000
        >>> str (c)
        '2001:db8:85a3::/48'
        >>> d = IP6_Address ('2001:db8:0:0:1:1:0:1')
        >>> str (d)
        '2001:db8::1:1:0:1'
        >>> e = IP6_Address ('2001:db8:0:1:1:0:0:1')
        >>> str (e)
        '2001:db8:0:1:1::1'
        >>> adr = IP6_Address ('2001:db8::')
        >>> adr in IP6_Address ('2001:db8::', 16)
        True
        >>> adr in IP6_Address ('2001:db8::', 24)
        True
        >>> adr in IP6_Address ('2001:db8:dead:beef::', 16)
        True
        >>> adr in IP6_Address ('2001:db8:dead:beef::', 48)
        False
        >>> adr.contains (IP6_Address ('2001:db8:dead:beef::', 48))
        False
        >>> f = IP6_Address ('2001:db8:dead:beef::', 48)
        >>> f.overlaps (f)
        True
        >>> f.overlaps (IP6_Address (f.ip, 16))
        True
        >>> f = IP6_Address (f.ip, 16)
        >>> f
        2001::/16
        >>> f.overlaps (f)
        True
        >>> g = IP6_Address ('2001:db8:dead:beef:1234:5678:9abc:def0')
        >>> f.overlaps (g)
        True
        >>> g.overlaps (g)
        True
        >>> g.overlaps (IP6_Address (g.ip + (1 << 96), 32))
        False
        >>> g.overlaps (IP6_Address (g.ip + (2 << 96), 32))
        False
        >>> print "%x" % g.ip
        20010db8deadbeef123456789abcdef0
        >>> print "%x" % g.bitmask
        ffffffffffffffffffffffffffffffff
        >>> g
        2001:db8:dead:beef:1234:5678:9abc:def0
        >>> g == g
        True
        >>> g == f
        False
        >>> f
        2001::/16
        >>> f == IP6_Address ('2001:db8::')
        False
        >>> f.contains (IP6_Address ('2001:db8::'))
        True
        >>> f == IP6_Address ('2001:db8::', 16)
        True
        >>> list (sorted ((a, b, c, d, e, f, g)))
        [2001::/16, 2001:db8::1:1:0:1, 2001:db8:0:1:1::1, 2001:db8:85a3::/64, 2001:db8:85a3::/48, 2001:db8:85a3::8a2e:370:7334, 2001:db8:dead:beef:1234:5678:9abc:def0]
        >>> i5 = IP6_Address ('2001:db8::/126')
        >>> print "0x%X" % i5.bitmask
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
        >>> len (i5)
        4
        >>> i5.len ()
        4L
        >>> print "0x%x" % i5._broadcast
        0x20010db8000000000000000000000003
        >>> i5.netblk
        [2001:db8::, 2001:db8::3]
        >>> for i in i5 :
        ...     print i
        2001:db8::
        2001:db8::1
        2001:db8::2
        2001:db8::3
        >>> for i in i5.subnets () :
        ...     print i
        2001:db8::
        2001:db8::1
        2001:db8::2
        2001:db8::3
        >>> for i in i5.subnets (24) :
        ...     print i
        >>> for i in i5.subnets (127) :
        ...     print i
        2001:db8::/127
        2001:db8::2/127
        >>> i1 = IP6_Address ('2001:db8::/16')
        >>> i2 = IP6_Address ('2001:db8:dead:beef::/16')
        >>> d = dict.fromkeys ((i1, i2))
        >>> d
        {2001::/16: None}
        >>> IP6_Address ('2001:db8::/129')
        Traceback (most recent call last):
         ...
        ValueError: Invalid netmask: 129
        >>> IP6_Address ('20001:db8::')
        Traceback (most recent call last):
         ...
        ValueError: Hex value too long: 20001
        >>> IP6_Address ('1:2:3:4:5:6:7:8:9')
        Traceback (most recent call last):
         ...
        ValueError: Too many hex parts in address: 1:2:3:4:5:6:7:8:9
        >>> IP6_Address (':1:2:3:4:5:6:7:8')
        Traceback (most recent call last):
         ...
        ValueError: No single ':' at start allowed
        >>> IP6_Address ('1:2:3:4:5:6:7:8:')
        Traceback (most recent call last):
         ...
        ValueError: No single ':' at end allowed
        >>> IP6_Address ('1:2:3:4:::6:7:8')
        Traceback (most recent call last):
         ...
        ValueError: Too many ':': 1:2:3:4:::6:7:8
        >>> IP6_Address ('1:2:4::6::7:8')
        Traceback (most recent call last):
         ...
        ValueError: Only one '::' allowed
    """

    bitlen = 128L

    def _to_str (self) :
        r    = []
        ip   = self.ip
        moff = 0
        mlen = 0
        off  = 0
        l    = 0
        for i in xrange (8) :
            v = ip & 0xFFFF
            r.append ("%x" % v)
            if v :
                if l > mlen :
                    moff = off
                    mlen = l
                off = i + 1
                l   = 0
            else :
                l += 1
            ip >>= 16
        if l > mlen :
            moff = off
            mlen = l
        repl = ''
        if moff == 0 or moff + mlen == 8 :
            repl = ':'
        if mlen :
            r [moff : moff + mlen] = [repl]
        r = ':'.join (reversed (r))
        return r
    # end def _to_str

    def _from_string (self, adr) :
        """ Compute numeric ipv6 address from adr without netmask.
        """
        if adr.startswith (':') :
            if not adr.startswith ('::') :
                raise ValueError, "No single ':' at start allowed"
            if adr != '::' and adr.endswith (':') :
                raise ValueError, "No ':' at start and end"
        elif adr.endswith (':') :
            if not adr.endswith ('::') :
                raise ValueError, "No single ':' at end allowed"
        lower = ''
        upper = adr.split ('::')
        if len (upper) > 2 :
            raise ValueError, "Only one '::' allowed"
        if len (upper) > 1 :
            upper, lower = upper
        else :
            upper = upper [0]

        value = 0L
        shift = self.bitlen - 16

        count = 0
        if upper :
            for v in upper.split (':') :
                if not v :
                    raise ValueError, "Too many ':': %s" % adr
                if len (v) > 4 :
                    raise ValueError, "Hex value too long: %s" % v
                v = long (v, 16)
                if shift < 0 :
                    raise ValueError, "Too many hex parts in address: %s" % adr
                value |= v << shift
                shift -= 16
                count += 1
        if lower :
            lv = 0L
            for v in lower.split (':') :
                if not v :
                    raise ValueError, "Too many ':': %s" % adr
                if len (v) > 4 :
                    raise ValueError, "Hex value too long: %s" % v
                v = long (v, 16)
                lv <<= 16
                lv |=  v
                count += 1
            value |= lv
        if count > 8 :
            raise ValueError, "Too many hex parts in address: %s" % adr
        self.ip = value
    # end def _from_string

# end class IP6_Address


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
