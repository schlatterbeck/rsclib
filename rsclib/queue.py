#!/usr/bin/python

from rsclib.autosuper import autosuper

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

    level_map = {} # for naming

    def __init__ (self, parent = None, **kw) :
        self.parent   = parent
        self._depth   = None
        self._number  = None
        self.__super.__init__ (**kw)
        if self.parent :
            self.parent.register (self)
    # end def __init__

    def ind (self, indent = None) :
        indent = indent or self.depth
        return '   ' * (indent - 1)
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
        return ':'.join ((str (self.depth), str (self.number)))
    # end def name

    @property
    def number (self) :
        if self._number :
            return self._number
        if self.depth not in self.level_map :
            self._number = self.level_map [self.depth]  = 1
        else :
            self.level_map [self.depth] += 1
            self._number = self.level_map [self.depth]
        return self._number
    # end def number

    @property
    def parentname (self) :
        if not self.parent :
            return '1:'
        return self.parent.name
    # end def parentname

    def __getitem__ (self, key) :
        return getattr (self, key)
    # end def __getitem__

# end class Traffic_Shaping_Object

class Traffic_Leaf (Traffic_Shaping_Object) :
    """ Leaf in a Traffic shaping hierarchy.
    """
    weight = 1 # when parent calls weightsum
# end class Traffic_Leaf

class SFQ_Leaf (Traffic_Leaf) :
    def generate (self, kbit_per_second, wsum, dev) :
        l = locals ()
        self.result = []
        self.outp ('tc qdisc add dev %(dev)s %%(name)s sfq perturb 10' % l)
        return '\n'.join (self.result)
    # end def generate
# end class SFQ_Leaf

class RED_Leaf (Traffic_Leaf) :
    def generate (self, kbit_per_second, wsum, dev) :
        l = locals ()
        self.result = []
        self.outp ('')
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
        Detection as leaf-qdisc. For bulk TCP traffic it is desirable to
        do early drop of packets to minimize bulk retransmits when
        dropping everything at the queue tail due to overflow.  We use
        this information to output a Linux traffic shaping configuration
        using HFSC qdisc/class. The leaf qdisc will be RED in case of
        bulk traffic and SFQ in case of non-bulk traffic.
    """

    def __init__ (self, weight, size = 0, delay_ms = 0, is_bulk = False, **kw) :
        self.weight   = weight
        self.size     = size
        self.delay_ms = delay_ms
        self.is_bulk  = is_bulk
        self.__super.__init__ (**kw)
    # end def __init__

    def generate (self, kbit_per_second, wsum, dev) :
        rate   = float (self.weight) / wsum * kbit_per_second
        nonlin = ''
        if self.size and self.delay_ms and not self.children :
            nonlin = ' umax %(size)sb dmax %(delay_ms)sms' % self
        l = locals ()
        self.result = []
        self.outp ('tc class add dev %(dev)s parent %%(parentname)s \\' % l)
        self.outp ('   classid %(name)s hfsc \\')
        self.outp ('   sc rate %(rate)skbit%(nonlin)s \\' % l)
        self.outp ('   ul rate %(kbit_per_second)skbit'  % l)
        if not self.children :
            if self.is_bulk :
                RED_Leaf (parent = self)
            else :
                SFQ_Leaf (parent = self)
        for c in self.children :
            self.result.append \
                (c.generate (kbit_per_second, self.weightsum, dev))
        return '\n'.join (self.result)
    # end def generate

# end class Traffic_Class

class Shaper (Weighted_Bandwidth) :
    """ Top-Level container of Traffic_Class(es), this gets a list of
        Traffic classes to install at top-level in an interface.
        The generator then generates the necessary statements to add the
        top-level qdisc (and delete it if it is already there).
    """
    def __init__ (self, *classes, **kw) :
        self.__super.__init__ (**kw)
        for c in classes :
            assert (not c.parent)
            self.register (c)
    # end def __init__
    
    def generate (self, kbit_per_second, dev) :
        s = []
        s.append \
            ( 'tc qdisc del dev %(dev)s root handle 1: hfsc 2> /dev/null'
            % locals ()
            )
        s.append ('tc qdisc add dev %(dev)s root handle 1: hfsc' % locals ())
        for c in self.children :
            s.append (c.generate (kbit_per_second, self.weightsum, dev))
        return '\n'.join (s)
    # end def generate
# end class Shaper

if __name__ == '__main__' :
    import sys

    root     = Traffic_Class (100)
    fast     = Traffic_Class (80, parent = root)
    express  = Traffic_Class ( 5, size =  128, delay_ms = 10, parent = fast)
    interact = Traffic_Class (20, size =  512, delay_ms = 15, parent = fast)
    vpn      = Traffic_Class (55, size = 1500, delay_ms = 20, parent = fast)
    slower   = Traffic_Class (20, parent = root)
    normal   = Traffic_Class \
        (25, size = 1500, delay_ms = 20, parent = slower, is_bulk = True)
    bulk     = Traffic_Class \
        (25, parent = slower, is_bulk = True)

    shaper   = Shaper (root)

    print >> sys.stdout, shaper.generate (2000, 'eth0')

