#!/usr/bin/python

from rsclib.autosuper import autosuper

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

    def gen_filter (self, dev) :
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

    def gen_filter (self, dev) :
        self.result = []
        for c in self.children :
            r = c.gen_filter (dev)
            if r :
                self.result.append (r)
        if self.is_leaf :
            assert (self.fwmark)
            l = locals ()
            f = '$TC filter add dev %(dev)s parent %%(rootname)s \\' % l
            self.outp (f)
            self.outp ('    protocol ip prio 1')
            self.outp ('    handle %(fwmark)s fw flowid %(name)s')
            if self.is_default :
                self.outp (f)
                self.outp ('    protocol ip prio 2 flowid %(name)s')
        return '\n'.join (self.result)
    # end def gen_filter

# end class Traffic_Class

class Shaper (Weighted_Bandwidth) :
    """ Top-Level container of Traffic_Class(es), this gets a list of
        Traffic classes to install at top-level in an interface.
        The generator then generates the necessary statements to add the
        top-level qdisc (and delete it if it is already there).
    """
    def __init__ (self, tc_cmd = '/sbin/tc', *classes, **kw) :
        self.tc_cmd = tc_cmd
        self.__super.__init__ (**kw)
        for c in classes :
            assert (not c.parent)
            self.register (c)
    # end def __init__
    
    def generate (self, kbit_per_second, dev) :
        s = []
        s.append ('TC=%s' % self.tc_cmd)
        s.append \
            ( '$TC qdisc del dev %(dev)s root handle 1: hfsc 2> /dev/null'
            % locals ()
            )
        s.append ('$TC qdisc add dev %(dev)s root handle 1: hfsc' % locals ())
        for c in self.children :
            s.append (c.generate (kbit_per_second, self.weightsum, dev))
        for c in self.children :
            s.append (c.gen_filter (dev))
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
    TC ( 5,  128, delay_ms = 10, parent = fast,                 fwmark = 10)
    # interactive
    TC (20,  512, delay_ms = 15, parent = fast,                 fwmark = 11)
    # vpn
    TC (55, 1500, delay_ms = 20, parent = fast,                 fwmark = 12)
    # normal
    TC (25, 1500, delay_ms = 20, parent = slow, is_bulk = True, fwmark = 13)
    # bulk
    TC (25,      is_default = 1, parent = slow, is_bulk = True, fwmark = 14)

    shaper   = Shaper ('/bin/tc', root)

    print >> sys.stdout, shaper.generate (2000, 'eth0')

