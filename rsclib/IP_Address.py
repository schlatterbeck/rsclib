#!/usr/bin/python
# Copyright (C) 2005-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__          import print_function
from rsclib.autosuper    import _autosuper
from rsclib.pycompat     import with_metaclass, string_types, long_type, longpr
from rsclib.pycompat     import assert_raises
from rsclib.iter_recipes import xxrange as xrange
from functools           import total_ordering


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
                raise ValueError \
                    ( "IP4_Address: Syntax: Invalid Octet: %s in %s"
                    % (octet, s)
                    )
        elif v == 255 :
            mask += 8
        elif v in mask_bits :
            mask += mask_bits [v]
            zero = True
        else :
            raise ValueError \
                ("IP4_Address: Syntax: Invalid Octet: %s in %s" % (octet, s))
    return mask
# end def netmask_from_string

class _IP_Meta_ (_autosuper) :
    """ Since IP_Address objects are immutable we return the given
        object itself if we're passed an instance of our class.
        So the copy-constructor effectively doesn't return a copy but
        the object itself.
    """

    def __call__ (self, arg, * args, ** kw) :
        if isinstance (arg, self) :
            return arg
        return _autosuper.__call__ (self, arg, * args, ** kw)
    # end def __call__

    @property
    def bitlen (self) :
        return self._bitlen
    # end def bitlen

# end class _IP_Meta_

class IP_Meta (with_metaclass (_IP_Meta_)) :
    pass
# end class IP_Meta

@total_ordering
class IP_Address (IP_Meta) :

    _bitlen = None

    def __init__ (self, address, mask = None, strict_mask = False) :
        if mask is None :
            mask  = self._bitlen
        self._mask = long_type (mask)
        if self._mask < 0 or self._mask > self._bitlen :
            raise ValueError \
                (self._esyntax_ ("Invalid netmask: %s" % self._mask))
        if isinstance (address, string_types) :
            xadr = address.split ('/', 1)
            if len (xadr) > 1 :
                m = int (xadr [1])
                if m < 0 or m > self._bitlen :
                    raise ValueError \
                        (self._esyntax_ ("Invalid netmask: %s" % m))
                self._mask = min (self._mask, m)
            self._from_string (xadr [0])
        else :
            self._ip = long_type (address)
        if self._ip >= (1 << self._bitlen) :
            raise ValueError (self._esyntax_ ("Invalid ip: %s" % address))
        self._bitmask = ((1 << self._mask) - 1) << (self._bitlen - self._mask)
        self._invmask = (~long_type (self._bitmask)) & ((1 << self._bitlen) - 1)
        if strict_mask and (self._ip & self._bitmask) != self._ip :
            raise ValueError \
                (self._esyntax_ ("Bits to right of netmask not zero"))
        self._ip &= self._bitmask
    # end def __init__

    @property
    def bitlen (self) :
        return self._bitlen
    # end def bitlen

    @property
    def bitmask (self) :
        return self._bitmask
    # end def bitmask

    @property
    def _broadcast (self) :
        return self._ip | self._invmask
    # end def _broadcast

    @property
    def broadcast_address (self) :
        return self.__class__ (self._broadcast)
    # end def broadcast_address

    broadcast = broadcast_address

    @property
    def invmask (self) :
        return self._invmask
    # end def invmask

    @property
    def ip (self) :
        return self._ip
    # end def ip

    @property
    def mask (self) :
        return self._mask
    # end def mask

    mask_len = mask

    @property
    def net (self) :
        return self.__class__ (self._ip)
    # end def net
    
    network = net

    @property
    def netblk (self) :
        return [self.__class__ (x) for x in (self._ip, self._broadcast)]
    # end def netblk

    @property
    def parent (self) :
        if self._mask > 0 :
            return self.__class__ (self._ip, self._mask - 1)
    # end def parent

    @property
    def subnet_mask (self) :
        return self.__class__ (self._bitmask)
    # end def subnet_mask

    netmask = subnet_mask

    def _clscheck_ (self, other) :
        ii = isinstance
        if not ii (other, self.__class__) and not ii (self, other.__class__) :
            return False
        return True
    # end def _clscheck_

    def contains (self, other) :
        other = self._cast_ (other)
        if not self._clscheck_ (other) :
            return False
        return other.mask >= self.mask and self.ip == (other.ip & self.bitmask)
    # end def contains

    def overlaps (self, other) :
        other = self._cast_ (other)
        if not self._clscheck_ (other) :
            return False
        return \
            (  self.ip &  self.bitmask == other.ip &  self.bitmask
            or self.ip & other.bitmask == other.ip & other.bitmask
            )
    # end def overlaps

    def is_sibling (self, other) :
        other = self._cast_ (other)
        if not self._clscheck_ (other) :
            return False
        if self._mask != other._mask :
            return False
        srt = tuple (sorted ((self, other)))
        return srt == tuple (self.parent.subnets (self._mask))
    # end def is_sibling

    def subnets (self, mask = None) :
        if mask is None :
            mask = self._bitlen
        inc = 1 << (self._bitlen - mask)
        if mask < self._mask :
            raise StopIteration
        # xrange doesn't support long ints :-( see xxrange import above
        for i in xrange (0, self._broadcast - self._ip + 1, inc) :
            yield self.__class__ (i + self._ip, mask)
    # end def subnets

    def __eq__ (self, other) :
        if not self._clscheck_ (other) :
            return type (self) == type (other)
        return self.ip == other.ip and self.mask == other.mask
    # end def __eq__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __lt__ (self, other) :
        if not self._clscheck_ (other) :
            return id (type (self)) < id (type (other))
        if self.ip == other.ip :
            return self.mask < other.mask
        return self.ip < other.ip
    # end def __lt__

    __contains__ = contains

    def __eq__ (self, other) :
        other = self._cast_ (other)
        if not self._clscheck_ (other) :
            return False
        return self.ip == other.ip and self.mask == other.mask
    # end def __eq__

    def __hash__ (self) :
        return str (self).__hash__ ()
    # end def __hash__

    __iter__ = subnets

    def __len__ (self) :
        return self._broadcast - self._ip + 1
    # end def __len__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __nonzero__ (self) :
        """ An IP address is always non-zero, even the 0 Address.
        """
        return True
    # end def __nonzero__
    __bool__ = __nonzero__

    def __repr__ (self) :
        ret = self._to_str ()
        if self._mask != self._bitlen :
            ret += '/%s' % self._mask
        return ret
    # end def __repr__

    __str__  = __repr__

    def _cast_ (self, other) :
        if not isinstance (other, self.__class__) :
            try :
                other = self.__class__ (other)
            except (ValueError, TypeError) :
                pass
        return other
    # end def _cast_

    def _esyntax_ (self, s) :
        return "%s: Syntax: %s" % (self.__class__.__name__, s)
    # end def _esyntax_

    # dangerous, put last to avoid conflict with built-in len
    # we keep this for compatibility with IPy
    len = __len__

# end def IP_Address

class IP4_Address (IP_Address) :
    """
        IP version 4 Address with optional subnet mask.
        >>> a = IP4_Address ('10.100.10.0')
        >>> longpr (a.mask)
        32L
        >>> "%s" % a.mask
        '32'
        >>> a.bitlen
        32
        >>> "%s" % a.bitlen
        '32'
        >>> a.__class__.bitlen
        32
        >>> a.parent
        10.100.10.0/31
        >>> longpr (a.ip)
        174328320L
        >>> longpr (a._broadcast)
        174328320L
        >>> str (a)
        '10.100.10.0'
        >>> a = IP4_Address (u'10.100.10.0')
        >>> str (a)
        '10.100.10.0'
        >>> aa = IP4_Address ('10.36.48.129', '255.255.255.224')
        >>> longpr (aa.mask)
        27L
        >>> longpr (aa.mask_len)
        27L
        >>> str (aa)
        '10.36.48.128/27'
        >>> b = IP4_Address ('10.100.10.5', 24)
        >>> longpr (b.ip)
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
        >>> longpr (b.ip)
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
        >>> longpr (c.ip)
        174325760L
        >>> str (c)
        '10.100.0.0/16'
        >>> d = IP4_Address ('10.100.0.0/24', 16)
        >>> longpr (d.ip)
        174325760L
        >>> str (d)
        '10.100.0.0/16'
        >>> str (d.subnet_mask)
        '255.255.0.0'
        >>> print (d.subnet_mask)
        255.255.0.0
        >>> d.broadcast_address
        10.100.255.255
        >>> d.net
        10.100.0.0
        >>> e = IP4_Address ('10.100.0.0')
        >>> longpr (e.ip)
        174325760L
        >>> str (e)
        '10.100.0.0'
        >>> str (IP4_Address (174325760))
        '10.100.0.0'
        >>> str (IP4_Address (65535))
        '0.0.255.255'
        >>> IP4_Address (0xFFFFFFFF)
        255.255.255.255
        >>> adr = IP4_Address ('10.100.10.1')
        >>> adr.parent
        10.100.10.0/31
        >>> adr.is_sibling (IP4_Address ('10.100.10.0'))
        True
        >>> adr.is_sibling (IP4_Address ('10.100.10.2'))
        False
        >>> zz = IP4_Address ('10.101.0.0/16')
        >>> zz.is_sibling (IP4_Address ('10.100.0.0/16'))
        True
        >>> zz.is_sibling (IP4_Address ('10.102.0.0/16'))
        False
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
        >>> f == IP4_Address (str (g), f.mask)
        True
        >>> class zoppel (IP4_Address) : pass
        >>> f == zoppel (str (g), f.mask)
        True
        >>> f.overlaps (g)
        True
        >>> g.overlaps (g)
        True
        >>> g.overlaps (IP4_Address ('10.101.10.2', 32))
        False
        >>> g.overlaps (IP4_Address ('10.100.10.3', 32))
        False
        >>> longpr (g.ip, g.bitmask)
        174328322L 4294967295L
        >>> g
        10.100.10.2
        >>> g == g
        True
        >>> g == '10.100.10.2'
        True
        >>> g == '10.100.10.2/32'
        True
        >>> g != '10.100.10.2'
        False
        >>> g != '10.100.10.3'
        True
        >>> g <  '10.100.10.3'
        False
        >>> g <= '10.100.10.3'
        False
        >>> g >= '10.100.10.3'
        True
        >>> g > '10.100.10.3'
        True
        >>> g <= '10.100.10.2'
        True
        >>> g <= '10.100.10.1'
        False
        >>> g >  '10.100.10.1'
        True
        >>> g >= '10.100.10.1'
        True
        >>> g >= '10.100.10.2'
        True
        >>> g >= '10.100.10.3'
        True
        >>> '10.100.10.2/32' in g
        True
        >>> '10.100.10.2/30' in g
        False
        >>> '10.100.10.2' in IP4_Address ('10.100.10.0/24')
        True
        >>> g == None
        False
        >>> None == g
        False
        >>> g == 'something-invalid'
        False
        >>> 'something-invalid' == g
        False
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
        [10.100.0.0/16, 10.100.0.0/16, 10.100.0.0/16, 10.100.0.0, 10.100.10.0/24, 10.100.10.0, 10.100.10.2]
        >>> IP4_Address ('108.62.8.0/21').netblk
        [108.62.8.0, 108.62.15.255]
        >>> i5 = IP4_Address ('10.23.5.0/30')
        >>> print ("0x%X" % i5.bitmask)
        0xFFFFFFFC
        >>> len (i5)
        4
        >>> longpr (i5.len ())
        4L
        >>> longpr (i5._broadcast)
        169280771L
        >>> i5.netblk
        [10.23.5.0, 10.23.5.3]
        >>> for i in i5 :
        ...     print (i)
        10.23.5.0
        10.23.5.1
        10.23.5.2
        10.23.5.3
        >>> for i in i5.subnets () :
        ...     print (i)
        10.23.5.0
        10.23.5.1
        10.23.5.2
        10.23.5.3
        >>> for i in i5.subnets (24) :
        ...     print (i)
        >>> for i in i5.subnets (31) :
        ...     print (i)
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
        ValueError: IP4_Address: Syntax: Invalid netmask: 33
        >>> IP4_Address ('256.2.3.4')
        Traceback (most recent call last):
         ...
        ValueError: IP4_Address: Syntax: Invalid octet: 256
        >>> IP4_Address ('1.2.3.4.5')
        Traceback (most recent call last):
         ...
        ValueError: IP4_Address: Syntax: Too many octets: 1.2.3.4.5
        >>> IP4_Address ('1.2.4.3/22', strict_mask = True)
        Traceback (most recent call last):
         ...
        ValueError: IP4_Address: Syntax: Bits to right of netmask not zero

        >>> x1 = IP4_Address ('1.2.3.4')
        >>> bool (x1)
        True
        >>> bool (IP4_Address ('0.0.0.0'))
        True
        >>> bool (IP4_Address ('192.168.0.96/27'))
        True
        >>> x2 = IP4_Address (x1)
        >>> x1 == x2
        True
        >>> x1 is x2
        True
        >>> sub = 'argument must be a string'
        >>> assert_raises (TypeError, sub, IP6_Address, x1)
    """

    _bitlen = 32

    def __init__ (self, address, mask = _bitlen, **kw) :
        if isinstance (mask, string_types) and len (mask) > 3 :
            mask = netmask_from_string (mask)
        self.__super.__init__ (address, mask, **kw)
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
        ip = self._ip
        r = []
        for i in range (4) :
            r.append (ip & 255)
            ip >>= 8
        return '.'.join (str (k) for k in reversed (r))
    # end def dotted
    _to_str = dotted

    def _from_string (self, address) :
        a = 0
        for n, octet in enumerate (address.split ('.')) :
            a <<= 8
            v = long_type (octet)
            if not (0 <= v <= 255) :
                raise ValueError \
                    (self._esyntax_ ("Invalid octet: %s" % octet))
            a |= long_type (octet)
            if n > 3 :
                raise ValueError \
                    (self._esyntax_ ("Too many octets: %s" % address))
        self._ip = a
    # end def _from_string

# end class IP4_Address

class IP6_Address (IP_Address) :
    """
        IP version 6 Address with optional subnet mask.
        >>> a = IP6_Address ("::")
        >>> longpr (a.mask)
        128L
        >>> "%s" % a.mask
        '128'
        >>> a.bitlen
        128
        >>> "%s" % a.bitlen
        '128'
        >>> a.__class__.bitlen
        128
        >>> longpr (a.ip)
        0L
        >>> longpr (a._broadcast)
        0L
        >>> a = IP6_Address ("::1")
        >>> a.parent
        ::/127
        >>> a.is_sibling (IP6_Address ("::"))
        True
        >>> a.is_sibling (IP6_Address ("::2"))
        False
        >>> a.is_sibling (IP6_Address (a.ip, a.mask - 1))
        False
        >>> longpr (a.ip)
        1L
        >>> a = IP6_Address ("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        >>> print ("%X" % a.ip)
        20010DB885A3000000008A2E03707334
        >>> print ("%X" % IP6_Address ("2001:db8:85a3:0:0:8a2e:370:7334").ip)
        20010DB885A3000000008A2E03707334
        >>> print ("%X" % IP6_Address ("2001:db8:85a3::8a2e:370:7334").ip)
        20010DB885A3000000008A2E03707334
        >>> print ("%X" % IP6_Address ("2001:db8:85a3::").ip)
        20010DB885A300000000000000000000
        >>> print ("%X" % IP6_Address ("::8a2e:370:7334").ip)
        8A2E03707334
        >>> str (a)
        '2001:db8:85a3::8a2e:370:7334'
        >>> b = IP6_Address ('2001:db8:85a3::8a2e:370:7334', 64)
        >>> print ("%X" % b.ip)
        20010DB885A300000000000000000000
        >>> str (IP6_Address (0x20010DB885A300000000000000000000))
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
        >>> longpr (c.mask)
        48L
        >>> longpr (c.mask_len)
        48L
        >>> b in c
        True
        >>> c in b
        False
        >>> print ("%X" % c.ip)
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
        >>> f == IP6_Address (str (g), f.mask)
        True
        >>> class zoppel (IP6_Address) : pass
        >>> f == zoppel (str (g), f.mask)
        True
        >>> g == g
        True
        >>> g == '2001:db8:dead:beef:1234:5678:9abc:def0'
        True
        >>> g == '2001:db8:dead:beef:1234:5678:9abc:def0/128'
        True
        >>> g == '2001:db8:dead:beef:1234:5678:9abc:def1'
        False
        >>> g != '2001:db8:dead:beef:1234:5678:9abc:def0'
        False
        >>> g != '2001:db8:dead:beef:1234:5678:9abc:def1'
        True
        >>> g <  '2001:db8:dead:beef:1234:5678:9abc:def1'
        False
        >>> g <= '2001:db8:dead:beef:1234:5678:9abc:def1'
        False
        >>> g <= '2001:db8:dead:beef:1234:5678:9abc:def0'
        True
        >>> g <= '2001:db8:dead:beef:1234:5678:9abc:deef'
        False
        >>> g >  '2001:db8:dead:beef:1234:5678:9abc:deef'
        True
        >>> g >= '2001:db8:dead:beef:1234:5678:9abc:deef'
        True
        >>> g >= '2001:db8:dead:beef:1234:5678:9abc:def0'
        True
        >>> g >= '2001:db8:dead:beef:1234:5678:9abc:def1'
        True
        >>> '2001:db8:dead:beef:1234:5678:9abc:def0' in g
        True
        >>> '2001:db8:dead:beef:1234:5678:9abc:def0/128' in g
        True
        >>> '2001:db8:dead:beef:1234:5678:9abc::/112' in g
        False
        >>> zz = IP6_Address ('2001:db8:dead:beef:1234:5678:9abc::/112')
        >>> '2001:db8:dead:beef:1234:5678:9abc:def0' in zz
        True
        >>> g == None
        False
        >>> None == g
        False
        >>> g == 'something-invalid'
        False
        >>> 'something-invalid' == g
        False
        >>> f.overlaps (g)
        True
        >>> g.overlaps (g)
        True
        >>> g.overlaps (IP6_Address (g.ip + (1 << 96), 32))
        False
        >>> g.overlaps (IP6_Address (g.ip + (2 << 96), 32))
        False
        >>> print ("%x" % g.ip)
        20010db8deadbeef123456789abcdef0
        >>> print ("%x" % g.bitmask)
        ffffffffffffffffffffffffffffffff
        >>> g
        2001:db8:dead:beef:1234:5678:9abc:def0
        >>> g == g
        True
        >>> g == f
        False
        >>> f
        2001::/16
        >>> f.parent
        2000::/15
        >>> f.is_sibling (IP6_Address ("2000::/16"))
        True
        >>> f.is_sibling (IP6_Address ("2002::/16"))
        False
        >>> f.is_sibling (f.parent)
        False
        >>> f == IP6_Address ('2001:db8::')
        False
        >>> f.contains (IP6_Address ('2001:db8::'))
        True
        >>> f == IP6_Address ('2001:db8::', 16)
        True
        >>> list (sorted ((a, b, c, d, e, f, g)))
        [2001::/16, 2001:db8::1:1:0:1, 2001:db8:0:1:1::1, 2001:db8:85a3::/48, 2001:db8:85a3::/64, 2001:db8:85a3::8a2e:370:7334, 2001:db8:dead:beef:1234:5678:9abc:def0]
        >>> i5 = IP6_Address ('2001:db8::/126')
        >>> i5.mask
        126
        >>> i5.mask_len
        126
        >>> print ("0x%X" % i5.bitmask)
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
        >>> len (i5)
        4
        >>> longpr (i5.len ())
        4L
        >>> print ("0x%x" % i5._broadcast)
        0x20010db8000000000000000000000003
        >>> i5.netblk
        [2001:db8::, 2001:db8::3]
        >>> for i in i5 :
        ...     print (i)
        2001:db8::
        2001:db8::1
        2001:db8::2
        2001:db8::3
        >>> for i in i5.subnets () :
        ...     print (i)
        2001:db8::
        2001:db8::1
        2001:db8::2
        2001:db8::3
        >>> for i in i5.subnets (24) :
        ...     print (i)
        >>> for i in i5.subnets (127) :
        ...     print (i)
        2001:db8::/127
        2001:db8::2/127
        >>> i32 = IP6_Address ('2001:db8::/32')
        >>> for i in i32.subnets (33) :
        ...     print (i)
        2001:db8::/33
        2001:db8:8000::/33
        >>> i1 = IP6_Address ('2001:db8::/16')
        >>> i2 = IP6_Address ('2001:db8:dead:beef::/16')
        >>> d = dict.fromkeys ((i1, i2))
        >>> d
        {2001::/16: None}
        >>> IP6_Address ('2001:db8::/129')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Invalid netmask: 129
        >>> IP6_Address ('20001:db8::')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 20001
        >>> IP6_Address ('1:2:3:4:5:6:7:8:9')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Too many hex parts in 1:2:3:4:5:6:7:8:9
        >>> IP6_Address (':1:2:3:4:5:6:7:8')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: No single ':' at start allowed
        >>> IP6_Address ('1:2:3:4:5:6:7:8:')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: No single ':' at end allowed
        >>> IP6_Address ('1:2:3:4:::6:7:8')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Too many ':': 1:2:3:4:::6:7:8
        >>> IP6_Address ('1:2:4::6::7:8')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Only one '::' allowed
        >>> IP6_Address ('2001:0db8:85a3:0000:0000:8a2e:0370:7334')
        2001:db8:85a3::8a2e:370:7334
        >>> IP6_Address ('2001:db8:85a3:0:0:8a2e:370:7335')
        2001:db8:85a3::8a2e:370:7335
        >>> IP6_Address ('2001:db8:85a3::8a2e:370:7336')
        2001:db8:85a3::8a2e:370:7336
        >>> IP6_Address ('2001:0db8:0000:0000:0000:0000:1428:57ab')
        2001:db8::1428:57ab
        >>> IP6_Address ('2001:0db8:0000:0000:0000::1428:57ac')
        2001:db8::1428:57ac
        >>> IP6_Address ('2001:0db8:0:0:0:0:1428:57ad')
        2001:db8::1428:57ad
        >>> IP6_Address ('2001:0db8:0:0::1428:57ae')
        2001:db8::1428:57ae
        >>> IP6_Address ('2001:0db8::1428:57af')
        2001:db8::1428:57af
        >>> IP6_Address ('2001:db8::1428:57b0')
        2001:db8::1428:57b0
        >>> IP6_Address ('0000:0000:0000:0000:0000:0000:0000:0001')
        ::1
        >>> IP6_Address ('::1')
        ::1
        >>> IP6_Address ('::ffff:0c22:384e')
        ::ffff:c22:384e
        >>> IP6_Address ('2001:0db8:1234:0000:0000:0000:0000:0000')
        2001:db8:1234::
        >>> IP6_Address ('2001:0db8:1234:ffff:ffff:ffff:ffff:ffff')
        2001:db8:1234:ffff:ffff:ffff:ffff:ffff
        >>> IP6_Address ('2001:db8:a::123')
        2001:db8:a::123
        >>> IP6_Address ('fe80::')
        fe80::
        >>> IP6_Address ('::ffff:c000:280')
        ::ffff:c000:280
        >>> IP6_Address ('::')
        ::
        >>> IP6_Address ('::ffff:12.34.56.78')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 12.34.56.78
        >>> IP6_Address ('::ffff:192.0.2.128')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 192.0.2.128
        >>> IP6_Address ('123')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Not enough hex parts in 123
        >>> IP6_Address ('ldkfj')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: ldkfj
        >>> IP6_Address ('2001::FFD3::57ab')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Only one '::' allowed
        >>> IP6_Address ('2001:db8:85a3::8a2e:37023:7334')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 37023
        >>> assert_raises (ValueError, 'invalid literal', IP6_Address, '2001:db8:85a3::8a2e:370k:7334')
        >>> IP6_Address ('1::2::3')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Only one '::' allowed
        >>> IP6_Address ('1:::3:4:5')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Too many ':': 1:::3:4:5
        >>> IP6_Address ('1:2:3::4:5:6:7:8:9')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Too many hex parts in 1:2:3::4:5:6:7:8:9
        >>> IP6_Address ('::ffff:2.3.4')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 2.3.4
        >>> IP6_Address ('::ffff:257.1.2.3')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 257.1.2.3
        >>> IP6_Address ('1.2.3.4')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Hex value too long: 1.2.3.4
        >>> IP6_Address (':aa:aa:aa')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: No single ':' at start allowed
        >>> IP6_Address ('aa:aa:aa:')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: No single ':' at end allowed
        >>> IP6_Address ('1:2:3:4:5:6:7')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Not enough hex parts in 1:2:3:4:5:6:7
        >>> IP6_Address (':::')
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: No ':' at start and end
        >>> IP6_Address ('1::2/126', strict_mask = True)
        Traceback (most recent call last):
         ...
        ValueError: IP6_Address: Syntax: Bits to right of netmask not zero
        >>> x1 = IP6_Address ('2001:0db8::1')
        >>> bool (x1)
        True
        >>> bool (IP6_Address ('::'))
        True
        >>> bool (IP6_Address ('2001:0db8::/64'))
        True
        >>> x2 = IP6_Address (x1)
        >>> x1 == x2
        True
        >>> x1 is x2
        True
        >>> assert_raises (TypeError, 'must be a string', IP4_Address, x1)
    """

    _bitlen = 128

    def _to_str (self) :
        r    = []
        ip   = self._ip
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
        if moff == 0 :
            repl = repl + ':'
        if moff + mlen == 8 :
            repl = repl + ':'
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
                raise ValueError \
                    (self._esyntax_ ("No single ':' at start allowed"))
            if adr != '::' and adr.endswith (':') :
                raise ValueError (self._esyntax_ ("No ':' at start and end"))
        elif adr.endswith (':') :
            if not adr.endswith ('::') :
                raise ValueError \
                    (self._esyntax_ ("No single ':' at end allowed"))
        lower = ''
        upper = adr.split ('::')
        if len (upper) > 2 :
            raise ValueError (self._esyntax_ ("Only one '::' allowed"))
        if len (upper) > 1 :
            upper, lower = upper
            double_colon = True
        else :
            upper = upper [0]
            double_colon = False

        value = 0
        shift = self._bitlen - 16

        count = 0
        if upper :
            for v in upper.split (':') :
                if not v :
                    raise ValueError \
                        (self._esyntax_ ("Too many ':': %s" % adr))
                if len (v) > 4 :
                    raise ValueError \
                        (self._esyntax_ ("Hex value too long: %s" % v))
                v = long_type (v, 16)
                if shift < 0 :
                    raise ValueError \
                        (self._esyntax_ ("Too many hex parts in %s" % adr))
                value |= v << shift
                shift -= 16
                count += 1
        if lower :
            lv = 0
            for v in lower.split (':') :
                if not v :
                    raise ValueError \
                        (self._esyntax_ ("Too many ':': %s" % adr))
                if len (v) > 4 :
                    raise ValueError \
                        (self._esyntax_ ("Hex value too long: %s" % v))
                try :
                    v = long_type (v, 16)
                except ValueError as msg :
                    raise ValueError (self._esyntax_ (msg))
                lv <<= 16
                lv |=  v
                count += 1
            value |= lv
        if count > 8 :
            raise ValueError \
                (self._esyntax_ ("Too many hex parts in %s" % adr))
        if not double_colon and count < 8 :
            raise ValueError \
                (self._esyntax_ ("Not enough hex parts in %s" % adr))
        self._ip = value
    # end def _from_string

# end class IP6_Address


if __name__ == "__main__" :

    import sys

    def interfaces (ip, mask) :
        x = IP4_Address (ip, mask)
        print ("address %s" % ip)
        print ("netmask %s" % x.subnet_mask ())
        print ("network %s" % x.net ())
        print ("broadcast %s" % x.broadcast_address ())
    # end def interfaces

    interfaces (sys.argv [1], int (sys.argv [2]))
