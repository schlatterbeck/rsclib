#!/usr/bin/python
# Copyright (C) 2010-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from re                  import compile as rc
from functools           import total_ordering
from rsclib.autosuper    import autosuper
from rsclib.stateparser  import Parser
from rsclib.IP_Address   import IP4_Address
from rsclib.iter_recipes import pairwise, ranges

@total_ordering
class Port (autosuper) :
    """ A Nmapped port with the protocol, port number, the scanned state
        and the service.
        >>> ports = [Port (21, 'tcp', 'open', 'ftp')]
        >>> ports.append (Port (5001, 'tcp', 'open', 'commplex-link'))
        >>> ports.append (Port (21, 'tcp', 'open', 'ftp'))
        >>> ports.sort ()
        >>> ports
        [Port (21, tcp, open, ftp), Port (21, tcp, open, ftp), Port (5001, tcp, open, commplex-link)]
    """
    template = "%-9s %-8s %s"
    def __init__ (self, port, protocol, state, service) :
        self.port     = int (port)
        self.protocol = protocol
        self.state    = state
        self.service  = service
    # end def __init__

    def __eq__ (self, other) :
        return self.protocol == other.protocol and self.port == other.port
    # end def __eq__

    def __ne__ (self, other) :
        return not self == other
    # end def __ne__

    def __lt__ (self, other) :
        if self.protocol == other.protocol :
            return self.port < other.port
        return self.protocol < other.protocol
    # end def __lt__

    def __repr__ (self) :
        return "Port (%s, %s, %s, %s)" \
            % (self.port, self.protocol, self.state, self.service)
    # end def __repr__

    def __str__ (self) :
        return self.template % \
            ("%s/%s" % (self.port, self.protocol) , self.state, self.service)
    # end def __str__
# end class Port

class Host (autosuper) :
    """ A Target-Host of nmap """
    def __init__ \
        ( self
        , ip
        , name   = None
        , state  = "filtered"
        , count  = 0
        , state2 = None
        , count1 = 0
        , count2 = 0
        ) :
        self.count    = int (count)
        self.count1   = int (count1)
        self.count2   = int (count2)
        self.macaddr  = None
        self.macname  = None
        self.name     = name
        self.state    = state
        self.state2   = state2
        self.ip       = IP4_Address (ip)
        self.ports    = []
        self.warnings = []
    # end def __init__

    def add_mac (self, macaddr, macname) :
        self.macaddr = macaddr
        self.macname = macname or ''
    # end def add_mac

    def add_port (self, port) :
        self.ports.append (port)
        self.count += 1
    # end def add_port

    def add_warnings (self, warnings) :
        self.warnings = warnings [:]
    # end def add_warnings

    def equivalent (self, other, except_dict = {}) :
        """ Check if two host have equivalent scan results. An optional
            exception dictionary considers them non-equivalent if one
            (or both) are found in the dict.
        """
        if str (self.ip) in except_dict or str (other.ip) in except_dict :
            return False
        return \
            (   self.ports  == other.ports
            and self.state  == other.state
            and self.state2 == other.state2
            )
    # end def equivalent

    @property
    def is_filtered (self) :
        return self.state == 'filtered' and not self.ports and not self.state2
    # end def is_filtered

    def state_ports (self, state) :
        return [p.port for p in self.ports if p.state == state]
    # end def state_ports

    def state_ports_tex (self, state, threshold = None) :
        """ Return closed ports as comma separated list with contiguous
            ranges replace by a range (double dash for TeX)
        """
        ret = []
        first = None
        ports = sorted (self.state_ports (state))
        if not ports :
            return '--'
        if len (ports) == self.count :
            return 'all'
        elif threshold and len (ports) > self.count * threshold :
            return "[%s %s ports]" % (self.count, state)
        for p1, p2 in ranges (ports) :
            if p1 == p2 :
                ret.append (str (p1))
            elif p1 + 1 == p2 :
                ret.append ('%s, %s' % (p1, p2))
            else :
                ret.append ('%s--%s' % (p1, p2))
        return ', '.join (ret)
    # end def state_ports_tex

    def __cmp__ (self, other) :
        return (  cmp (self.ip, other.ip)
               or cmp (self.ports, other.ports)
               )
    # end def __cmp__

    def __repr__ (self) :
        ret = []
        ret.append \
            ( 'Host (%s, name = %s, state = %s, count = %s'
            % (self.ip, self.name, self.state, self.count)
            )
        if self.state2 :
            ret.append \
                ( ' state2 = %s count1 = %s count2 = %s)'
                % (self.state2, self.count1, self.count2)
                )
        ret.append (''.join (x))
        for p in self.ports :
            ret.append (repr (p))
        if self.macaddr :
            mn = ''
            if self.macname :
                mn = ' (%s)' % self.macname
            ret.append ('MAC Address: %s%s' % (self.macaddr, mn))
        return '\n'.join (ret)
    # end def __repr__

    def __str__ (self) :
        ret  = []
        name = self.ip
        plen = len (self.ports)
        if self.name :
            name = "%s (%s)" % (self.name, self.ip)
        for w in self.warnings :
            ret.append (w)
        if plen :
            rest = self.count - plen
            ret.append ("Interesting ports on %s:" % name)
            if rest :
                ret.append ("Not shown: %s %s ports" % (rest, self.state))
            ret.append (Port.template % ('PORT', 'STATE', 'SERVICE'))
        else :
            x = []
            x.append \
                ( "All %s scanned ports on %s are %s"
                % (self.count, name, self.state)
                )
            if self.state2 :
                x.append \
                    ( ' (%s) or %s (%s)'
                    % (self.count1, self.state2, self.count2)
                    )
            ret.append (''.join (x))
        for p in self.ports :
            ret.append (str (p))
        if self.macaddr :
            mn = ''
            if self.macname :
                mn = ' (%s)' % self.macname
            ret.append ('MAC Address: %s%s' % (self.macaddr, mn))
        ret.append ('')
        return '\n'.join (ret)
    # end def __str__
# end class Host

class NMAP (autosuper) :
    list = []

    def __init__ (self, version, date) :
        self.version = version
        self.date    = date # FIXME: convert
        self.hosts   = []
        self.list.append (self)
    # end def __init__

    @classmethod
    def as_tex \
        ( cls
        , caption          = None
        , label            = None
        , no_filtered      = False
        , ip_map           = {}
        , thresh_open      = None
        , thresh_closed    = None
        , paragraph_open   = None
        , paragraph_closed = None
        ) :
        """ Build TeX table of open/closed ports from all nmap objects.
            Table is compressed if several adjacent hosts have the same
            open/closed ports.

            Optionally add a caption and a label to the generated TeX
            table.

            if no_filtered is specified, we don't show hosts with all
            ports filtered.

            Some ip addresses may be explicitly printed with a name by
            specifying the ip/name pair in ip_map. Those explicitly
            named ips are not affected by no_filtered.

            If paragraph_open/_closed are specified, we generate a p{length}
            element for the list of ports instead of "r". The given
            length is the paragraph_open/_closed parameter.
        """
        ret   = []
        ret.append (r"\begin{table}[htb]")
        ret.append (r"\begin{center}")
        para_open = para_closed = "r"
        if paragraph_open :
            para_open   = "p{%s}" % paragraph_open
        if paragraph_closed :
            para_closed = "p{%s}" % paragraph_closed
        ret.append (r"{\footnotesize\begin{tabular}{r@{.}r@{.}r@{.}r@{}l%s%s}"
                   % (para_open, para_closed)
                   )
        ret.append (r"\multicolumn{5}{r}{IP-Adresse} &  Open & Closed \\")
        hosts = []
        for nmap in cls.list :
            for h in nmap.hosts :
                if  (  not no_filtered
                    or not h.is_filtered
                    or str (h.ip) in ip_map
                    ) :
                    hosts.append (h)
        for h1, h2 in ranges \
            ( sorted (hosts, key = lambda x: (str (x.ip) in ip_map, x))
            , lambda x : x.ip.ip
            , lambda x, y : x.equivalent (y, ip_map)
            ) :
            #print ("DEBUG:", h1, h2)
            x1 = str (h1.ip).replace ('.', '&')
            if h1.ip.ip == h2.ip.ip :
                x2 = ''
            else :
                l1 = str (h1.ip).split ('.')
                l2 = str (h2.ip).split ('.')
                x2 = []
                for o1, o2 in reversed (zip (l1, l2)) :
                    if o1 == o2 :
                        break
                    x2.append (o2)
                x2 = '--' + '.'.join (reversed (x2))
            po = h1.state_ports_tex ('open',   threshold = thresh_open)
            pc = h1.state_ports_tex ('closed', threshold = thresh_closed)
            if po == '--' and h1.state == 'open' :
                po = 'all'
            if pc == '--' and h1.state == 'closed' :
                pc = 'all'
            if pc == '--' and h1.state == 'filtered' and h1.state2 == 'closed' :
                pc = '[%s closed ports]' % h1.count2
            if str (h1.ip) in ip_map :
                assert (not x2)
                x = r"\multicolumn{5}{l}{%s}" % ip_map [str (h1.ip)]
            else :
                x = ' & '.join ((x1, x2))
            ret.append (r"%s & %s & %s \\" % (x, po, pc))
        ret.append (r"\end{tabular}\vspace*{-4mm}}")
        ret.append (r"\end{center}")
        if caption :
            ret.append (r"\caption{%s}" % caption)
        if label :
            ret.append (r"\label{%s}" % label)
        ret.append (r"\end{table}")
        return '\n'.join (ret)
    # end def as_tex

    def as_string (self, no_filtered = False) :
        if no_filtered and self.is_filtered :
            return ''
        ret = ['']
        ret.append \
            ( "Starting Nmap %s ( http://nmap.org ) at %s"
            % (self.version, self.date)
            )
        for h in self.hosts :
            if not no_filtered or not h.is_filtered :
                ret.append (str (h))
        adr_suf = host_suf = ''
        if self.n_address > 1 :
            adr_suf = 'es'
        if self.n_up > 1 :
            host_suf = 's'
        ret.append \
            ( "Nmap done: %s IP address%s "
              "(%d host%s up) scanned in %.3f seconds"
            % (self.n_address, adr_suf, self.n_up, host_suf, self.time)
            )
        return '\n'.join (ret)
    # end def as_string

    def add_host (self, host) :
        self.hosts.append (host)
    # end def add_host

    def done (self, n_address, n_up, state, time) :
        self.n_address = int (n_address)
        self.n_up      = int (n_up)
        self.state     = state
        self.time      = float (time)
    # end def done

    @property
    def is_filtered (self) :
        for h in self.hosts :
            if not h.is_filtered :
                return False
        return True
    # end def is_filtered

    def __repr__ (self) :
        ret = []
        ret.append ("NMAP (%s, %s, %s)" % self.n_address, self.n_up, self.time)
        for h in self.hosts :
            ret.append (repr (h))
        return '\n'.join (ret)
    # end def __repr__

    __str__ = as_string
# end class NMAP

class NMAP_Parser (Parser) :
    """ Parses an nmap log (several scans) into a list of NMAP objects """
    re_addr  =     r"([a-zA-Z0-9.-]+)( \(([a-zA-Z0-9.-]+)\))?"
    re_port  = rc (r"([0-9]+)/(\S+)\s+(\S+)\s+(\S+)")
    re_nmap  = rc (r"Starting Nmap ([0-9.]+) [(][^)]+[)] at (.*)$")
    re_done  = rc (r"Nmap (done|finished): (\d+) IP address[es]* "
                   r"[(](\d+) hosts? ([a-z]+)[)] scanned in ([0-9.]+) seconds"
                  )
    re_intr  = rc (r"Interesting ports on %(re_addr)s:" % locals ())
    re_start = rc (r"Nmap scan report for %(re_addr)s"  % locals ())
    re_or    =     r"( \((\d+)\) or ([a-z]+) \((\d+)\))?"
    re_show  = rc (r"Not shown: (\d+) ([a-z]+) ports")
    re_all   = rc ( r"All (\d+) scanned ports on %(re_addr)s "
                    r"are ([a-z]+)%(re_or)s$"
                  % locals ()
                  )
    re_md    =     r"[A-F0-9]{2}"
    re_mac   = rc ( r"MAC Address:\s+((%s:){5}%s)(\s+[(]([^)]+)[)])?"
                  % (re_md, re_md)
                  )
    re_up    = rc (r"Host is up(\s+\([0-9.]+s\s+latency\))?\.")
    re_warn  = rc (r"^Warning:(.*)$")
    re_plist = rc (r"PORT +STATE +SERVICE")
    re_empty = rc (r"^$")

    #State                  Pattern                new State          Action
    matrix = \
    [ ["init",            re_nmap,                  "started",     "start"]
    , ["init",            "",                       "init",        None]
    , ["started",         re_start,                 "interest",    "interest"]
    , ["started",         re_intr,                  "interest",    "interest"]
    , ["started",         re_all,                   "mac",         "do_all"]
    , ["started",         re_empty,                 "started",     None]
    , ["started",         re_warn,                  "started",     "warning"]
    , ["started",         re_done,                  "init",        "end"]
    , ["interest",        re_show,                  "interest",    "notshown"]
    , ["interest",        re_plist,                 "portlist",    None]
    , ["interest",        re_up,                    "interest",    None]
    , ["interest",        re_all,                   "mac",         "do_all"]
    , ["mac",             re_mac,                   "started",     "mac"]
    , ["mac",             None,                     "started",     None]
    , ["portlist",        re_port,                  "portlist",    "port"]
    , ["portlist",        re_empty,                 "started",     "pop"]
    , ["portlist",        re_mac,                   "started",     "mac"]
    ]


    def __init__ (self, *args, **kw) :
        self.warnings = []
        self.__super.__init__ (*args, **kw)
    # end def __init__

    def do_all (self, state, new_state, match) :
        g    = match.groups ()
        name, ip = self._get_name_and_ip (g [1], g [3])
        if self.nmap.hosts [-1].ip == ip :
            host = self.nmap.hosts [-1]
            assert host.name == name
        else :
            host = Host (ip, name)
            self.nmap.add_host (host)
        host.state  = g [4]
        host.count  = g [0]
        host.state2 = g [7]
        host.count1 = int (g [6] or 0)
        host.count2 = int (g [8] or 0)
        if self.warnings :
            host.add_warnings (self.warnings)
        self.warnings = []
    # end def do_all

    def end (self, state, new_state, match) :
        self.nmap.done (* match.groups () [1:])
    # end def end

    def interest (self, state, new_state, match) :
        g = match.groups ()
        name, ip = self._get_name_and_ip (g [0], g [2])
        host = Host (ip, name)
        if self.warnings :
            host.add_warnings (self.warnings)
        self.nmap.add_host (host)
        self.warnings = []
        return self.push (state, new_state, match)
    # end def interest

    def mac (self, state, new_state, match) :
        g = match.groups ()
        macaddr, macname = g [0], g [3]
        self.nmap.hosts [-1].add_mac (macaddr, macname)
    # end def mac

    def notshown (self, state, new_state, match) :
        g = match.groups ()
        host = self.nmap.hosts [-1]
        host.state = g [1]
        host.count = int (g [0])
    # end def notshown

    def port (self, state, new_state, match) :
        p = Port (* match.groups ())
        self.nmap.hosts [-1].add_port (p)
    # end def port

    def start (self, state, new_state, match) :
        self.nmap = NMAP (* match.groups ())
    # end def start

    def warning (self, state, new_state, match) :
        self.warnings.append (self.line.strip ())
    # end def warning

    def _get_name_and_ip (self, x1, x2) :
        ip   = x1
        name = None
        if x2 :
            name = ip
            ip   = x2
        return name, ip
    # end def _get_name_and_ip
# end class NMAP_Parser

def main () :
    import sys
    from optparse import OptionParser

    cmd = OptionParser ()
    cmd.add_option \
        ( "-t", "--as-tex"
        , dest    = "as_tex"
        , help    = "Output as LaTeX Table"
        , action  = "store_true"
        )
    cmd.add_option \
        ( "-n", "--no-filtered"
        , dest    = "no_filtered"
        , help    = "Don't output hosts where all ports are filtered"
        , action  = "store_true"
        )
    cmd.add_option \
        ( "-l", "--label"
        , dest    = "label"
        , help    = "TeX label for the output table"
        )
    cmd.add_option \
        ( "-c", "--caption"
        , dest    = "caption"
        , help    = "TeX caption for the output table"
        )
    cmd.add_option \
        ( "-i", "--named-ip"
        , dest    = "ip_map"
        , help    = "Name for ip in the form ip=name"
        , default = []
        , action  = "append"
        )
    cmd.add_option \
        ( "--threshold-open"
        , dest    = "thresh_open"
        , help    = "Threshold for summary info of open ports"
        , type    = float
        )
    cmd.add_option \
        ( "--threshold-closed"
        , dest    = "thresh_closed"
        , help    = "Threshold for summary info of closed ports"
        , type    = float
        )
    cmd.add_option \
        ( "--paragraph-open"
        , dest    = "paragraph_open"
        , help    = "Use paragraph TeX formatting for open ports"
        , default = ""
        )
    cmd.add_option \
        ( "--paragraph-closed"
        , dest    = "paragraph_closed"
        , help    = "Use paragraph TeX formatting for closed ports"
        , default = ""
        )
    (opt, args) = cmd.parse_args ()
    p = NMAP_Parser (verbose = 0)
    if len (args) == 0 :
        p.parse (sys.stdin)
    else :
        for fn in args :
            p.parse (open (fn))
    
    ip_map = {}
    for ipname in opt.ip_map :
        try :
            k, v = ipname.split ('=', 1)
        except ValueError :
            cmd.error ("named-ip (-i) option value must contain a '='")
        ip_map [k] = v
    if opt.as_tex :
        print \
            ( NMAP.as_tex \
                ( no_filtered      = opt.no_filtered
                , label            = opt.label
                , caption          = opt.caption
                , ip_map           = ip_map
                , thresh_open      = opt.thresh_open
                , thresh_closed    = opt.thresh_closed
                , paragraph_open   = opt.paragraph_open
                , paragraph_closed = opt.paragraph_closed
                )
            )
    else :
        for n in NMAP.list :
            if not opt.no_filtered or not n.is_filtered :
                print (n.as_string (no_filtered = opt.no_filtered))
# end def main

if __name__ == '__main__' :
    main ()
