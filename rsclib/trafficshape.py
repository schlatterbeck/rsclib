#!/usr/bin/python3
# Copyright (C) 2010-21 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from operator          import or_
from functools         import reduce
from rsclib.autosuper  import autosuper
from rsclib.execute    import Exec
from rsclib.IP_Address import IP4_Address

class Major_Counter (autosuper) :
    def __init__ (self, value = 0) :
        self.value = value
    # end def __init__

    def inc (self, amount = 1) :
        self.value += amount
        return self.value
    # end def inc

    def get_next (self) :
        return self.inc ()
    # end def get_next
# end class Major_Counter

class Weighted_Bandwidth (autosuper) :

    def __init__ (self, **kw) :
        self.children = []
        self.__super.__init__ (**kw)
    # end def __init__

    def register (self, child) :
        self.children.append (child)
    # end def register

    @property
    def weightsum (self) :
        w = 0.0
        for c in self.children :
            w += c.weight
        return w
    # end def weightsum

# end class Weighted_Bandwidth

class Traffic_Shaping_Object (autosuper) :

    major_counter = Major_Counter ()
    counter       = 1

    def __init__ (self, parent = None, **kw) :
        self.parent   = parent
        self._depth   = None
        self._number  = None
        self.__super.__init__ (**kw)
        if self.parent :
            self.parent.register (self)
    # end def __init__

    def gen_filter (self, dev, realdev) :
        pass
    # end def gen_filter

    def ind (self, indent = None) :
        indent = indent or self.depth
        return '    ' * (indent - 1)
    # end def ind

    def outp (self, ostr, indent = None) :
        self.result.append (''.join ((self.ind (indent), ostr % self)))
    # end def outp

    @property
    def depth (self) :
        if self._depth :
            return self._depth
        if not self.parent :
            self._depth = 1
        else :
            self._depth = self.parent.depth + 1
        return self._depth
    # end def depth

    @property
    def name (self) :
        return ':'.join ((str (self.major_no), str (self.number)))
    # end def name

    @property
    def number (self) :
        if self._number is not None :
            return self._number
        self._number = self.__class__.counter
        self.__class__.counter += 1
        return self._number
    # end def number

    @property
    def parentname (self) :
        if not self.parent :
            return '1:'
        return self.parent.name
    # end def parentname

    @property
    def rootname (self) :
        if not self.parent :
            return self.parentname
        return self.parent.rootname
    # end def rootname

    def __getitem__ (self, key) :
        return getattr (self, key)
    # end def __getitem__

# end class Traffic_Shaping_Object

class Traffic_Leaf (Traffic_Shaping_Object) :
    """ Leaf in a Traffic shaping hierarchy.
    """
    weight   = 1 # when parent calls weightsum

    @property
    def name (self) :
        return ':'.join ((str (self.major_counter.get_next ()), ''))
    # end def name

    def generate (self, kbit_per_second, wsum, dev) :
        self.result = []
        self.outp \
            ( '$TC qdisc add dev %(dev)s parent %%(parentname)s '
              'handle %%(name)s \\'
            % locals ()
            )
    # end def generate
# end class Traffic_Leaf

class SFQ_Leaf (Traffic_Leaf) :
    def generate (self, kbit_per_second, wsum, dev) :
        self.__super.generate (kbit_per_second, wsum, dev)
        self.outp ('    sfq perturb 10')
        return '\n'.join (self.result)
    # end def generate
# end class SFQ_Leaf

class RED_Leaf (Traffic_Leaf) :
    def generate (self, kbit_per_second, wsum, dev) :
        """ For details on RED parameter selection, see 
            M. Christiansen, K. Jeffay, D. Ott, and F.D. Smith 
            "Tuning RED for Web Traffic"
            ACM/IEEE Transactions on Networking, 2001. 
            http://www.cs.unc.edu/~jeffay/papers/IEEE-ToN-01.pdf
            Another good source is
            http://www.icir.org/floyd/REDparameters.txt
            All my sources (see above) seem to agree on a drop rate of
            0.1 but OpenWRT is using 0.12. OpenWRT claims that a drop
            probability somewhere between 0.1 and 0.2 should be a good
            tradeoff between link utilization and response time (0.1:
            response; 0.2: utilization) so I'm using 0.1 here.
            Other chosen settings stolen from OpenWRT qos script.
        """
        self.__super.generate (kbit_per_second, wsum, dev)
        av    = 1500 # pkt size
        rmin  = int (kbit_per_second * 1024 / 8 * 0.05) # 50 ms queue
        if rmin < 3000 : # at least 2 max-size pkts
            rmin = 3000
        rmax  = 3 * rmin
        limit = 3 * (rmin + rmax)
        burst = int ((2 * rmin + rmax) / (3 * av))
        if burst < 2 :
            burst = 2
        l     = locals ()
        self.outp ('    red min %(rmin)s max %(rmax)s burst %(burst)s \\'  % l)
        self.outp ('    avpkt %(av)s limit %(limit)s probability 0.1 ecn' % l)
        return '\n'.join (self.result)
    # end def generate
# end class RED_Leaf

class Traffic_Class (Traffic_Shaping_Object, Weighted_Bandwidth) :
    """ Model a class of traffic that needs to have certain bandwidth
        guarantees.
        We give a class a weight (used to calculate the overall
        bandwidth this class receives from its parent, all weights of
        all siblings are summed up, a class receives its share from the
        sum) and optionally the size (of packets or e.g.  framesize for
        video when a video frame consists of several packets), the
        realtime delay and optionally a parent Traffic_Class object.
        Optionally is_bulk can be specified to use Random Early
        Detection (RED) as leaf-qdisc. For bulk TCP traffic it is
        desirable to do early drop of packets to minimize bulk
        retransmits when dropping everything at the queue tail due to
        overflow.  We use this information to output a Linux traffic
        shaping configuration using HFSC qdisc/class. The leaf qdisc
        will be RED in case of bulk traffic and Stochastic Fairness
        Queuing (SFQ) in case of non-bulk traffic.

        A note on the default class (is_default setting): This sets the
        default option on the top-level hfsc qdisc. If this is not
        specified, traffic that is not properly marked is dropped. In my
        experience this *includes* ARP traffic. That means if no default
        is specified and you don't take special precautions for ARP, no
        communication is possible (if you're on ethernet).
    """

    major_no = Traffic_Shaping_Object.major_counter.get_next ()

    def __init__ \
        ( self
        , weight
        , size       = 0
        , delay_ms   = 0
        , is_bulk    = False
        , fwmark     = None
        , is_default = False
        , **kw
        ) :
        self.weight     = weight
        self.size       = size
        self.delay_ms   = delay_ms
        if fwmark :
            fwmark = '/'.join ("0x%x" % int (f, 0) for f in fwmark.split ('/'))
        self.fwmark     = fwmark
        self.is_bulk    = is_bulk
        self.is_default = is_default
        self.is_leaf    = False
        self.__super.__init__ (**kw)
    # end def __init__

    def generate (self, kbit_per_second, wsum, dev) :
        rate   = float (self.weight) / wsum * kbit_per_second
        nonlin = ''
        if self.size and self.delay_ms and not self.children :
            nonlin = 'umax %(size)sb dmax %(delay_ms)sms ' % self
        l = locals ()
        self.result = []
        self.outp \
            ( '$TC class add dev %(dev)s parent %%(parentname)s '
              'classid %%(name)s hfsc \\'
            % l
            )
        self.outp ('    sc %(nonlin)srate %(rate)skbit \\' % l)
        self.outp ('    ul rate %(kbit_per_second)skbit'  % l)
        if not self.children :
            self.is_leaf = True
            if self.is_bulk :
                RED_Leaf (parent = self)
            else :
                SFQ_Leaf (parent = self)
        for c in self.children :
            self.result.append \
                (c.generate (kbit_per_second, self.weightsum, dev))
        return '\n'.join (self.result)
    # end def generate

    def gen_filter (self, dev, realdev) :
        """ Generate tc filter configuration for given devices.
            The realdev is given if we redirect traffic from a real
            device to an ifb device for inbound shaping. In that case
            we generate the redirection rules from the real device to
            the ifb device by translating PREROUTING iptables mark rules
            to appropriate tc filters in both, the realdev (for marking
            and redirecting to the ifb dev) and the ifb dev (for rules
            that depend on previous marks and finally for redirecting to
            appropriate leaf qdiscs by fwmark).
        """
        self.result = []
        for c in self.children :
            r = c.gen_filter (dev, realdev)
            if r :
                self.result.append (r)
        if self.is_leaf :
            prio = 1
            assert (self.fwmark)
            l = locals ()
            if realdev :
                act = 'action mirred egress redirect dev %(dev)s' % l
                for r in IPTables_Mangle_Rule.rules :
                    if r.xmark != self.fwmark :
                        continue
                    if r.interface and r.interface != realdev :
                        continue
                    if r.mark :
                        flow = 'flowid %(name)s'
                        f = r.as_tc_filter (dev, self.rootname, replace = flow)
                        self.outp (f)
                    else :
                        f = r.as_tc_filter (realdev, 'ffff:', action = act)
                        self.outp (f)
                prio = IPTables_Mangle_Rule.maxprio ()

            f = '$TC filter add dev %(dev)s parent %%(rootname)s \\' % l
            l = locals ()
            self.outp (f)
            self.outp ('    protocol ip prio %(prio)s \\' % l)
            self.outp ('    handle %(fwmark)s fw flowid %(name)s')
            if self.is_default :
                prio += 1
                self.outp (f)
                self.outp ('    protocol ip prio %(prio)s \\' % locals ())
                self.outp ('    u32 match u8 0 0 flowid %(name)s')
        return '\n'.join (self.result)
    # end def gen_filter

    def get_default_name (self) :
        x = self.name # side effect: set numbers in depth first order
        if self.is_default :
            return self.name.split (':', 1) [1]
        if not self.is_leaf :
            for c in self.children :
                d = c.get_default_name ()
                if d :
                    return d
        return None
    # end def get_default_name

# end class Traffic_Class

class IPTables_Mangle_Rule (autosuper) :
    """ Represent an IPTables mangle rule.
        We parse the rule saved with the command ::

         iptables  -t mangle -S PREROUTING  -v

        this saves all prerouting rules used for traffic marking.
    """

    rules = []

    # for parsing saved iptables rules
    # Note: if there are multiple args, they are parsed right to left!
    #     option       nargs  (type, argument)* (reversed)
    options = \
        { '!'              : (0, ('bool',  'negate_option'))
        , '-A'             : (1, ('str',   'chain'))
        , '-c'             : (2, ('int',   'bytecount')
                               , ('int',   'pkgcount')
                             )
        , '-d'             : (1, ('str',   'destination'))
        , '-f'             : (0, ('bool',  'is_fragment'))
        , '-i'             : (1, ('str',   'interface'))
        , '-j'             : (1, ('str',   'action'))
        , '-m'             : (1, ('list',  'modules'))
        , '-p'             : (1, ('str',   'protocol'))
        , '-P'             : (2, ('str',   'policy')
                               , ('str',   'chain')
                             )
        , '-s'             : (1, ('str',   'source'))
        , '--ctmask'       : (1, ('str',   'ctmask'))
        , '--dport'        : (1, ('port',  'dports'))
        , '--dports'       : (1, ('port',  'dports'))
        , '--icmp-type'    : (1, ('str',   'icmp_type'))
        , '--length'       : (1, ('range', 'length'))
        , '--mark'         : (1, ('str',   'mark'))
        , '--nfmask'       : (1, ('str',   'nfmask'))
        , '--restore-mark' : (0, ('bool',  'restore'))
        , '--save-mark'    : (0, ('bool',  'save'))
        , '--set-xmark'    : (1, ('str',   'xmark'))
        , '--sport'        : (1, ('port',  'sports'))
        , '--sports'       : (1, ('port',  'sports'))
        , '--state'        : (1, ('str',   'state'))
        , '--tcp-flags'    : (2, ('str',   'tcp_flags_comp')
                               , ('str',   'tcp_flags_mask')
                             )
        }

    protocols = \
        { 'icmp' :  1
        , 'tcp'  :  6
        , 'udp'  : 17
        , 'esp'  : 50
        , 'ah'   : 51
        }

    _tcp_flags = \
        { 'CWR' : 0x80
        , 'ECE' : 0x40
        , 'URG' : 0x20
        , 'ACK' : 0x10
        , 'PSH' : 0x08
        , 'RST' : 0x04
        , 'SYN' : 0x02
        , 'FIN' : 0x01
        }

    def __init__ (self, line, use_ipt = False) :
        self.pkgcount       = 0
        self.bytecount      = 0
        self.restore        = False
        self.save           = False
        self.negate_option  = False
        self.negated        = {}
        self.action         = None
        self.chain          = None
        self.destination    = None
        self.dports         = []
        self.interface      = None
        self.icmp_type      = None
        self.is_fragment    = False
        self.length         = []
        self.mark           = None
        self.modules        = None
        self.policy         = None
        self.protocol       = None
        self.source         = None
        self.sports         = []
        self.state          = None
        self.xmark          = None
        self.tcp_flags_comp = None
        self.tcp_flags_mask = None
        self.use_ipt        = use_ipt
        self.parse (line)
        self.rules.append (self)
        self._prio          = len (self.rules) # for filter rules
    # end def __init__

    def u32_nexthdr (self, width, value, mask, at, op = '') :
        """ Hack: work-around for non-working nexthdr.
            This should really expand to "at nexthdr+%s" % at
            Or to "cmp(u%(width)s at %(at)s layer transport mask %(mask)s
                   eq %(value)s"
        """
        nexthdr = 20 # IP packet without options
        value   = int (value)
        mask    = int (mask)
        offset  = nexthdr + at
        if op :
            return \
                ( "cmp(u%(width)s at 0x%(offset)x mask 0x%(mask)x "
                  "%(op)s 0x%(value)x)"
                % locals ()
                )
        return \
            ( "u32(u%(width)s 0x%(value)x 0x%(mask)x at 0x%(offset)x)"
            % locals ()
            )
    # end def u32_nexthdr

    def as_iptables (self, prefix = None) :
        """ output as iptables rule, the prefix should be the iptables
            command, if not given, output only the options.
        """
        ret = []
        if prefix is not None :
            ret.append (prefix)
        if self.policy :
            ret.append ('-P %s %s' % (self.chain, self.policy))
        elif self.chain :
            ret.append ('-A %s' % self.chain)
        if self.source :
            if 'source' in self.negated :
                ret.append ('!')
            ret.append ('-s %s' % self.source)
        if self.destination :
            if 'destination' in self.negated :
                ret.append ('!')
            ret.append ('-d %s' % self.destination)
        if self.interface :
            if 'interface' in self.negated :
                ret.append ('!')
            ret.append ('-i %s' % self.interface)
        if self.state :
            assert ('state' in self.modules)
            ret.append ('-m state')
            ret.append ('--state %s' % self.state)
        if self.is_fragment :
            if 'is_fragment' in self.negated :
                ret.append ('!')
            ret.append ('-f')
        if self.protocol :
            if 'protocol' in self.negated :
                ret.append ('!')
            ret.append ('-p %s' % self.protocol)
        if self.mark :
            assert ('mark' in self.modules)
            ret.append ('-m mark')
            if 'mark' in self.negated :
                ret.append ('!')
            ret.append ('--mark %s' % self.mark)
        if self.icmp_type is not None :
            assert ('icmp' in self.modules)
            ret.append ('-m icmp')
            if 'icmp_type' in self.negated :
                ret.append ('!')
            ret.append ('--icmp-type %s' % self.icmp_type)
        if self.dports or self.sports or self.tcp_flags_mask :
            if 'tcp' in self.modules :
                ret.append ('-m tcp')
            if 'udp' in self.modules :
                ret.append ('-m udp')
            if self.tcp_flags_mask :
                if 'tcp_flags_mask' in self.negated :
                    ret.append ('!')
                ret.append \
                    ('--tcp-flags %s %s'
                    % (self.tcp_flags_mask, self.tcp_flags_comp)
                    )
            if self.sports or self.dports :
                if len (self.sports) > 1 or len (self.dports) > 1 :
                    assert ('multiport' in self.modules)
                    ret.append ('-m multiport')

            for p, x in ('s', self.sports), ('d', self.dports) :
                if not x :
                    continue
                if '%sports' % p in self.negated :
                    ret.append ('!')
                plist = ','.join (':'.join (str (a) for a in z) for z in x)
                ret.append ('--%sport%s %s' % (p, ['','s'][len (x) > 1], plist))
        if self.length :
            assert ('length' in self.modules)
            ret.append ('-m length')
            if 'length' in self.negated :
                ret.append ('!')
            ret.append ('--length %s' % ':'.join (str (i) for i in self.length))
        if self.pkgcount is not None and self.bytecount is not None :
            ret.append ('-c %d %d' % (self.pkgcount, self.bytecount))
        if self.action :
            ret.append ('-j %s' % self.action)
        if self.restore :
            ret.append ('--restore-mark')
        if self.save :
            ret.append ('--save-mark')
        if self.save or self.restore :
            ret.append ('--nfmask %s' % self.nfmask)
            ret.append ('--ctmask %s' % self.ctmask)
        if self.xmark :
            ret.append ('--set-xmark %s' % self.xmark)
        return ' '.join (ret)
    # end def as_iptables

    def as_tc_filter \
        (self, dev, parent, prio = None, action = None, replace = None) :
        """ Output rules as tc filter commands using the basic classifier
            and the xt (xtables, former ipt) action. In addition
            optionally add another action. If use_ipt is True we use the
            old-style 'ipt' action instead of the newer 'xt'.
            Default action is to mark the packet. This can be overridden
            with replace. In addition an additional action may be
            specified with action.
        """
        act = 'xt'
        if self.use_ipt :
            act = 'ipt'
        if prio is None :
            prio = self.prio
        if not self.xmark :
            return ''
        ret = []
        ret.append ("$TC filter add dev %(dev)s"    % locals ())
        ret.append ("protocol ip parent %(parent)s" % locals ())
        ret.append ("prio %(prio)s basic match '"   % locals ())

        r = []
        if self.source :
            r.append \
                ("%s%s"
                % ( self.neg ("source")
                  , IP4_Address (self.source).as_tc_basic_u32 ()
                  )
                )
        if self.destination :
            r.append \
                ("%s%s"
                % ( self.neg ("destination")
                  , IP4_Address (self.destination).as_tc_basic_u32 (is_dst = 1)
                  )
                )
        if self.mark :
            neg = self.neg ('mark')
            try :
                mark, mask = self.mark.split ('/')
                r.append ("%smeta(fwmark mask %s eq %s)" % (neg, mask, mark))
            except ValueError :
                r.append ("%smeta(fwmark eq %s)" % (neg, self.mask))
        if self.is_fragment :
            # bit 19-31 are fragment offset
            # according to iptables(8), is_fragment means "that the rule
            # only refers to second and further fragments of fragmented
            # packets". So a non-fragment *or first fragment* is 0 in
            # the lower 13 bit. So we negate this (and the negate option
            # is inverted).
            neg = self.neg ("is_fragment", invert = True)
            r.append ("%su32 (u16 0x1FFF 0 at 6)" % neg)
        if self.length :
            xx = []
            (lower, upper) = self.length
            if lower :
                xx.append ("meta(pkt_len gt %s)" % (lower - 1))
            if upper < 65535 :
                xx.append ("meta(pkt_len lt %s)" % (upper + 1))
            if len (xx) > 1 and self.neg ('length') :
                xx = "(%s)" % ' and '.join (xx)
            else :
                xx = ' and '.join (xx)
            r.append (self.neg ('length') + xx)
        if self.protocol :
            r.append \
                ( "%su32 (u8 0x%x 0xff at 0x9)"
                % ( self.neg ("protocol")
                  , self.protocols [self.protocol.lower ()]
                  )
                )
        if self.tcp_flags_comp :
            r.append \
                ( "%s%s"
                % ( self.neg ("tcp_flags_mask")
                  , self.u32_nexthdr
                        ( 16
                        , self.tcp_flags (self.tcp_flags_comp)
                        , self.tcp_flags (self.tcp_flags_mask)
                        , 0xC
                        )
                  )
                )
        if self.icmp_type is not None :
            try :
                type, code = self.icmp_type.split ('/')
                x = []
                x.append (self.u32_nexthdr (8, type, 0xff, 0))
                x.append (self.u32_nexthdr (8, code, 0xff, 1))
                if len (x) > 1 and self.neg ("icmp_type") :
                    r.append \
                        ("%s(%s)" % (self.neg ("icmp_type"), " and ".join (x)))
                else :
                    r.append \
                        ("%s%s" % (self.neg ("icmp_type"), " and ".join (x)))
            except ValueError :
                v = self.u32_nexthdr (8, self.icmp_type, 0xff, 0)
                r.append ("%s%s" % (self.neg ("icmp_type"), v))
        for t, pp, off in (("s", self.sports, 0), ("d", self.dports, 2)) :
            t = t + "ports"
            r_or = []
            for p in pp :
                if len (p) == 1 :
                    r_or.append (self.u32_nexthdr(16, p [0], 0xffff, off))
                else :
                    v = ' and '.join \
                        (( self.u32_nexthdr (16, p [0] - 1, 0xffff, off, 'gt')
                        ,  self.u32_nexthdr (16, p [1] + 1, 0xffff, off, 'lt')
                        ))
                    r_or.append (v)
            if r_or :
                r.append ('%s(%s)' % (self.neg (t), ' or '.join (r_or)))
        ret.append (' and '.join (r))
        ret.append ("'")
        if replace :
            ret.append (replace)
        else :
            ret.append ("action %s -j MARK --set-xmark %s" % (act, self.xmark))
        if action :
            ret.append (action)
        return ' '.join (ret)
    # end def as_tc_filter

    def neg (self, name, invert = False) :
        cond = name in self.negated
        if invert :
            cond = not cond
        if cond :
            return 'not '
        return ''
    # end def neg

    def parse (self, line) :
        nargs = 0
        opt   = None
        for arg in line.split () :
            name = None
            if not nargs :
                opt = self.options [arg]
                nargs = opt [0]
                if nargs == 0 :
                    assert (opt [1][0] == 'bool')
                    name = opt [1][1]
                    self.parse_bool (name)
            else :
                name = opt [nargs][1]
                method = getattr (self, 'parse_' + opt [nargs][0])
                method (name, arg)
                nargs -= 1
            if self.negate_option and name and name != 'negate_option' :
                self.negated [name] = True
                self.negate_option  = False
    # end def parse

    def parse_bool (self, name) :
        setattr (self, name, True)
    # end def parse_bool

    def parse_int (self, name, arg) :
        setattr (self, name, int (arg))
    # end def parse_int

    def parse_list (self, name, arg) :
        l = getattr (self, name)
        if l is None :
            l = []
            setattr (self, name, l)
        l.append (arg)
    # end def parse_list

    def parse_port (self, name, arg) :
        val = [[int (x) for x in a.split (':')] for a in arg.split (',')]
        setattr (self, name, val)
    # end def parse_port

    def parse_range (self, name, arg) :
        setattr (self, name, [int (a) for a in arg.split (':', 1)])
    # end def parse_str

    def parse_str (self, name, arg) :
        setattr (self, name, arg)
    # end def parse_str

    @property
    def prio (self) :
        return len (self.rules) - self._prio + 1
    # end def prio

    @classmethod
    def maxprio (cls) :
        return len (cls.rules) + 2
    # end def maxprio

    @classmethod
    def parse_prerouting_rules (cls, file = None, use_ipt = False) :
        """ Parse prerouting rules from file or iptables pipe.
        """
        if file is None :
            x = Exec ()
            lines = x.exec_pipe ('iptables -t mangle -S PREROUTING -v'.split ())
        else :
            lines = file.readlines ()
        for line in lines :
            cls (line, use_ipt)
    # end def parse_prerouting_rules

    def tcp_flags (self, flags) :
        return reduce (or_, (self._tcp_flags [f] for f in flags.split (',')), 0)
    # end def tcp_flags

# end class IPTables_Mangle_Rule

class Shaper (Weighted_Bandwidth) :
    """ Top-Level container of Traffic_Class(es), this gets a list of
        Traffic classes to install at top-level in an interface.
        The generator then generates the necessary statements to add the
        top-level qdisc (and delete it if it is already there).
    """
    def __init__ (self, tc_cmd = '/sbin/tc', *classes, **kw) :
        self.tc_cmd = tc_cmd
        self.__super.__init__ (**kw)
        self.use_ipt = False
        if 'use_ipt' in kw :
            self.use_ipt = kw ['use_ipt']
        for c in classes :
            assert (not c.parent)
            self.register (c)
    # end def __init__
    
    def generate (self, kbit_per_second, dev, rulefile = None) :
        """ Generate traffic shaping configuration.
            We need the bandwidth and the device. The device can be
            special: If we're using ifb for inbound shaping, we can
            specify the device as ifb=real, e.g. ifb0=eth0 -- this
            will generate tc filter actions for matching the right
            packets in the *inbound* path of eth0 (or whatever the
            *real* interface is named) by translating the PREROUTING
            mangle rules that mark packets for shaping into appropriate
            tc filter actions. Additional mangle rules are generated in
            the toplevel qdisc for ifb0 in addition to the rules we
            would normally generate (for sorting packets with the
            appropriate firewall marks into the correct buckets).
            Rules in PREROUTING of the real device that match packets
            which already carry a mark are instantiated as tc filters in
            the ifb device.
        """
        rdev = None
        if '=' in dev :
            dev, rdev = dev.split ('=', 1)
            IPTables_Mangle_Rule.parse_prerouting_rules \
                (rulefile, use_ipt = self.use_ipt)
        default = ''
        for c in self.children :
            default = c.get_default_name ()
            if default :
                default = ' default %s' % default
                break
        s = []
        l = locals ()
        s.append ('TC=%s' % self.tc_cmd)
        s.append ('$TC qdisc del dev %(dev)s root 2>&1 > /dev/null' % l)
        s.append ('$TC qdisc add dev %(dev)s root handle 1: hfsc%(default)s' %l)
        if rdev :
            # remove top-level qdisc in rdev and re-add
            s.append ('$TC qdisc del dev %(rdev)s ingress 2>&1 > /dev/null' % l)
            s.append ('$TC qdisc add dev %(rdev)s ingress' % l)
        for c in self.children :
            s.append (c.generate (kbit_per_second, self.weightsum, dev))
        for c in self.children :
            s.append (c.gen_filter (dev, rdev))
        # redirect everything else that wasn't marked:
        if rdev :
            prio = IPTables_Mangle_Rule.maxprio () + 2
            l = locals ()
            s.append ('$TC filter add dev %(rdev)s parent ffff: \\' % l)
            s.append ('    protocol ip prio %(prio)s u32 match u32 0 0 \\' % l)
            s.append ('    action mirred egress redirect dev %(dev)s' % l)
        return '\n'.join (s)
    # end def generate
# end class Shaper

if __name__ == '__main__' :
    import sys

    TC = Traffic_Class
    root = TC (100)
    fast = TC (80, parent = root)
    slow = TC (20, parent = root)
    # express
    TC ( 5,  128, delay_ms = 10, parent = fast,                 fwmark='1/0xf')
    # interactive
    TC (20,  512, delay_ms = 15, parent = fast,                 fwmark='2/0xf')
    # vpn
    TC (55, 1500, delay_ms = 20, parent = fast,                 fwmark='3/0xf')
    # normal
    TC (25, 1500, delay_ms = 20, parent = slow, is_bulk = True, fwmark='4/0xf')
    # bulk
    TC (25,      is_default = 1, parent = slow, is_bulk = True, fwmark='5/0xf')

    shaper   = Shaper ('/bin/tc', root)

    for bw, dev in (2000, 'eth0'), (1000, 'ifb0=eth0') :
        print \
            ( shaper.generate (bw, dev, rulefile = open ('prerouting.out'))
            , file = sys.stdout
            )
