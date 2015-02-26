#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-13 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import re
from rsclib.autosuper   import autosuper
from rsclib.stateparser import Parser
from rsclib.execute     import Exec, Exec_Error, Log
from rsclib.Config_File import Config_File
from rsclib.ast_probe   import Asterisk_Probe

class Config (Config_File) :

    def __init__ (self, config = 'ast_isdn', path = '/etc/ast_isdn') :
        self.__super.__init__ \
            ( path, config
            , ASTERISK_HOST         = 'localhost'
            , ASTERISK_MGR_ACCOUNT  = 'user'
            , ASTERISK_MGR_PASSWORD = 'secret'
            )
    # end def __init__

# end class Config

class ISDN_Interface (autosuper) :
    """ Represent an ISDN Interface.
    """

    def __init__ (self, name, architecture) :
        self.name         = name
        self.span         = name # default
        self.architecture = architecture
        self.ports        = {}
        self.status       = 'unknown'
        self.mode         = 'unknown'
        self.l1           = 'unknown'
        self.l2           = 'unknown'
        self.type         = architecture # default
    # end def __init__

    @property
    def bc (self) :
        if hasattr (self, 'basechan') :
            return int (self.basechan)
        return self._bc
    # end def bc

    @property
    def tc (self) :
        if hasattr (self, 'totchans') :
            return int (self.totchans)
        return self._tc
    # end def tc

    def register (self, port) :
        self.ports [port.number] = port
        if not hasattr (self, 'basechan') :
            ports = list (sorted (self.ports.iterkeys ()))
            self._tc = ports [-1] - ports [0]
            self._bc = ports [0]
    # end def register

    def update_layerinfo (self) :
        """ Update l1 and l2 info for xorcom interfaces.
        """
        if self.type == 'digital-BRI' :
            xi = self.x_iface = Xorcom_Interface (self.name)
            if xi.l1 :
                self.l1 = xi.l1
            if xi.l2 :
                self.l2 = xi.l2
    # end def update_layerinfo

# end def ISDN_Interface

class Xorcom_Interface (Parser) :
    """ Get additional information about a Xorcom BRI Basic Rate
        Interface via /proc/xpp/XBUS-NN/XPD-MM/bri_info (if existing).
        In particular the Alarm Info of Xorcom Interfaces (used to get
        layer 1 and layer 2 status of DAHDI ISDN Interfaces) isn't
        correct for Xorcom, they always display "OK" even if layer 1 is
        down.
    """

    re_layer = re.compile (r"^[0-9]+\s+Layer 1:\s+([A-Z]+)")
    re_dchan = re.compile (r"^D-Channel:.*[(]([a-z]+)\s?.*[)]$")

    #       State   Pattern   new State Action
    matrix = \
        [ [ "init", re_layer, "init",   "layer1"]
        , [ "init", re_dchan, "init",   "layer2"]
        , [ "init", None,     "init",   None    ]
        ]

    def __init__ (self, name, ** kw) :
        self.__super.__init__ (** kw)
        self.l1 = None
        self.l2 = None
        try :
            f = open ("/proc/xpp/%s/bri_info" % name, "r")
        except IOError :
            return
        self.parse (f)
        f.close ()
    # end def __init__

    def layer1 (self, state, new_state, match) :
        self.l1 = match.group (1).lower ()
    # end def layer1

    def layer2 (self, state, new_state, match) :
        self.l2 = 'down'
        if match.group (1) == 'alive' :
            self.l2 = 'up'
    # end def layer2

# end class Xorcom_Interface

class ISDN_Port (autosuper) :
    """ Represent an ISDN Port of one of several possible ISDN interface
        of Asterisk: Linux Call Router using chan_lcr, native DAHDI
        channels, and Xorcom modules (they also use the DAHDI stack but
        can provide more information using Xorcom-specific commands).
        Note that a port in this terminology is what dahdi calls a span.
        In mISDN an interface can group several physical interfaces
        called ports.
    """

    # legacy: was indexed by portnumber, now use architecture, too
    by_portnumber = {}

    # required keys for printing
    keys = dict.fromkeys \
        (( 'ifname'
         , 'interface'
         , 'l1'
         , 'l2'
         , 'mode'
         , 'name'
         , 'number'
         , 'status'
         , 'type'
         ))
    # ignore these for printing
    ignore = dict.fromkeys (('iface',))

    def __init__ (self, number, iface, name = None, ** kw) :
        self.number    = number
        self.iface     = iface
        self.name      = name
        if not self.name :
            self.name  = "%s" % self.number
        self._status   = kw.get ('status', None)
        self._mode     = kw.get ('mode',   None)
        self._l1       = kw.get ('l1',     None)
        self._l2       = kw.get ('l2',     None)
        self.usage     = kw.get ('usage')
        # register:
        self.iface.register (self)
        key = "%s/%s" % (self.architecture, number)
        self.by_portnumber [key] = self
    # end def __init__

    @property
    def channel (self) :
        return self.channel_with_offset ()
    # end def channel

    def channel_with_offset (self, offset = 0, force_dchan = False) :
        if self.architecture == 'LCR' :
            return 'LCR/%s' % self.interface
        if offset > self.iface.tc :
            raise ValueError ("Offset: %s > %s" % (offset, self.iface.tc))
        if  (   self.iface.type.startswith ('digital-')
            and self.iface.tc == 3
            and offset == self.iface.bc + self.iface.tc - 1
            and not force_dchan
            ) :
            raise ValueError ("D-Channel: %s" % (self.iface.bc + offset))
        return 'dahdi/%s' % (self.iface.bc + offset)
    # end def channel

    @property
    def interface (self) :
        """ Interface span number as string. """
        return str (self.iface.span)
    # end def interface

    @property
    def ifname (self) :
        return self.iface.name
    # end def ifname

    @property
    def mode (self) :
        return self._mode or self.iface.mode
    # end def mode

    @property
    def l1 (self) :
        return self._l1 or self.iface.l1
    # end def l1

    @property
    def l2 (self) :
        return self._l2 or self.iface.l2
    # end def l2

    @property
    def status (self) :
        return self._status or self.iface.status
    # end def status

    def __getattr__ (self, name) :
        if not hasattr (self, 'iface') :
            raise AttributeError ("My iface attribute is missing")
        return getattr (self.iface, name)
    # end def __getattr__

    def __str__ (self) :
        d = dict (self.__dict__)
        d.update ((k, getattr (self, k)) for k in self.keys.iterkeys ())
        for k in self.ignore.iterkeys () :
            del d [k]
        return ', '.join \
            ( "%s = %s"
            % (k, (repr (v), repr (v)[1:])[repr (v).startswith ('u')])
             for k, v in sorted (d.iteritems ())
             if k [0] != '_' and v is not None
            )
    # end def __str__
    
    def __repr__ (self) :
        return "%s (%s)" % (self.__class__.__name__, str (self))
    # end def __name__

# end class ISDN_Port


class LCR_Ports (Parser, Exec) :
    """ Represent all ISDN ports of Linux Call Router
        Parse the output of "lcradmin portinfo" and put the result into
        a nice data structure. For parsing we use the stateparser from
        rsclib.
    """

    re_empty = re.compile (r"^$")
    re_start = re.compile (r"^([0-9-a-zA-Z]+):\s*$")
    re_param = re.compile (r"\s+([-a-z0-9 ]*[a-zA-Z0-9])\s+=\s+(.*)$")
    re_port  = re.compile (r'^([0-9]+)\s+"([^"]*)"')

    #       State   Pattern   new State Action
    matrix = \
        [ [ "init", re_start, "port",   "port_start"]
        , [ "init", re_empty, "init",   None        ]
        , [ "port", re_param, "port",   "port_set"  ]
        , [ "port", None,     "init",   "pop"       ]
        ]

    attrs = \
        { 'extension' : None
        , 'l1 link'   : 'l1'
        , 'l2 link'   : 'l2'
        }

    def __init__ (self, parsestring = None, ** kw) :
        self.__super.__init__ (** kw)
        self.iface = None
        self.port  = None
        if parsestring :
            parsestring = parsestring.split ('\n')
        else :
            parsestring = self.exec_pipe (("lcradmin", "portinfo"))
        self.parse (parsestring)
    # end def __init__

    def port_start (self, state, new_state, match) :
        self.iface = ISDN_Interface (match.groups () [0].strip (), 'LCR')
        self.port  = None
        self.push (state, new_state, match)
    # end def port_start

    def port_set (self, state, new_state, match) :
        name, value = match.groups ()
        name = name.replace ('-', '_')
        name = self.attrs.get (name, name)
        if name == 'port' :
            m = self.re_port.match (value)
            number, name = m.groups ()
            number = int (number)
            self.port = ISDN_Port (number, self.iface, name)
        elif name == 'usage' :
            self.port.usage = int (value)
        elif name :
            if name in ('status', 'l1', 'l2', 'mode') :
                setattr (self.port, '_%s' % name, value)
            else :
                setattr (self.port, name, value)
    # end def port_set
# end class LCR_Ports

class DAHDI_Ports (Parser, Exec) :
    """ Represent all ISDN ports of DAHDI channels
        Parse the output of "dahdi_scan" and put the result into
        a nice data structure. For parsing we use the stateparser from
        rsclib.
    """

    re_empty = re.compile (r"^$")
    re_start = re.compile (r"^\[([0-9]+)\]$")
    re_param = re.compile (r"([-a-z0-9_]+)=\s*(.*)$")

    #       State   Pattern   new State Action
    matrix = \
        [ [ "init",  re_start, "iface",   "iface_start"]
        , [ "init",  re_empty, "init",    None         ]
        , [ "iface", re_param, "iface",   "iface_set"  ]
        , [ "iface", None,     "init",    "pop"        ]
        ]

    attrs = {}

    def __init__ (self, parsestring = None, ** kw) :
        self.__super.__init__ (** kw)
        self.iface = None
        self.port  = None
        if parsestring :
            parsestring = parsestring.split ('\n')
        else :
            parsestring = self.exec_pipe (("dahdi_scan",))
        self.parse (parsestring)
        if self.iface :
            self.iface.update_layerinfo ()
    # end def __init__

    def iface_start (self, state, new_state, match) :
        name       = match.group (1)
        number     = int (name)
        if self.iface :
            self.iface.update_layerinfo ()
        self.iface = ISDN_Interface (name, 'dahdi')
        p = ISDN_Port (number, self.iface)
        self.iface.span = number
        self.push (state, new_state, match)
    # end def iface_start

    def iface_set (self, state, new_state, match) :
        name, value = match.groups ()
        name = name.replace ('-', '_')
        name = self.attrs.get (name, name)
        assert name != 'mode' and name != 'status'
        if name == 'port' :
            num, type = value.split (',')
            #p = ISDN_Port (int (num), self.iface, num)
            #p.subtype = type
        else :
            setattr (self.iface, name, value)
        if name == 'alarms' :
            if value == 'OK' :
                self.iface.l1 = self.iface.l2 = 'up'
            else :
                self.iface.l1 = self.iface.l2 = 'down'
        if name == 'active' and value == 'yes' :
            self.iface.status = 'unblocked'
        if name == 'type' :
            if value == 'digital-NT' :
                self.iface.mode = 'NT-mode'
            if value == 'digital-TE' :
                self.iface.mode = 'TE-mode'
        if name == 'description' and value.startswith ('Xorcom') :
            t = value.split (':') [-1].strip ()
            if t == 'BRI_TE' :
                self.iface.mode = 'TE-mode'
            if t == 'BRI_NT' :
                self.iface.mode = 'NT-mode'
    # end def iface_set

# end class DAHDI_Ports

def lcr_init (** kw) :
    """ Parse once """
    try :
        LCR_Ports (** kw)
    except Exec_Error :
        pass
# end def lcr_init

class ISDN_Ports (Log) :

    def __init__ (self, config = 'ast_isdn', cfgpath = '/etc/ast_isdn', ** kw) :
        self.__super.__init__ (** kw)
        self.cfg     = cfg = Config (config = config, path = cfgpath)

        arch = self.cfg.get ('ISDN_ARCHITECTURE')
        if arch :
            arch = dict.fromkeys (arch)
        if 'architecture' in kw :
            d = kw ['architecture']
        elif arch :
            d = arch
        else :
            ap = Asterisk_Probe (cfg = self.cfg)
            d  = ap.probe_apps ()
            ap.close ()
        if 'lcr_config' in d or 'lcr' in d :
            lcr_init (** kw)
        if 'DAHDISendKeypadFacility' in d or 'dahdi' in d :
            DAHDI_Ports (** kw)
    # end def __init__

    def __iter__ (self) :
        return iter \
            ( sorted
                ( ISDN_Port.by_portnumber.itervalues ()
                , key = lambda x : (x.architecture, x.number)
                )
            )
    # end def __iter__

# end class ISDN_Ports

if __name__ == '__main__' :
    import sys

    lcr_output = """
Ext1:
         port = 0 "hfc-4s.1-1"
         extension = no
         status = unblocked
         mode = TE-mode ptp l2hold
         out-channel = any
         in-channel = free
         l1 link = up
         l2 link = up
         usage = 0
Ext2:
         port = 1 "hfc-4s.1-2"
         extension = no
         status = unblocked
         mode = TE-mode ptp l2hold
         out-channel = any
         in-channel = free
         l1 link = up
         l2 link = up
         usage = 0
Int:
         port = 2 "hfc-4s.1-3"
         extension = no
         status = unblocked
         mode = NT-mode ptp l2hold
         out-channel = free
         in-channel = free
         l1 link = up
         l2 link = up
         usage = 0
Int:
         port = 3 "hfc-4s.1-4"
         extension = no
         status = unblocked
         mode = NT-mode ptp l2hold
         out-channel = free
         in-channel = free
         l1 link = down
         l2 link = unknown
         usage = 0
"""
    dahdi_output = """
[1]
active=yes
alarms=RED
description=B4XXP (PCI) Card 0 Span 1
name=B4/0/1
manufacturer=Digium
devicetype=BeroNet BN4S0
location=PCI Bus 03 Slot 04
basechan=1
totchans=3
irq=0
type=digital-TE
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=B8ZS,AMI,HDB3
framing_opts=ESF,D4,CCS,CRC4
coding=AMI
framing=CCS
[2]
active=yes
alarms=UNCONFIGURED
description=B4XXP (PCI) Card 0 Span 2
name=B4/0/2
manufacturer=Digium
devicetype=BeroNet BN4S0
location=PCI Bus 03 Slot 04
basechan=4
totchans=3
irq=0
type=digital-TE
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=B8ZS,AMI,HDB3
framing_opts=ESF,D4,CCS,CRC4
coding=AMI
framing=CCS
[3]
active=yes
alarms=OK
description=B4XXP (PCI) Card 0 Span 3
name=B4/0/3
manufacturer=Digium
devicetype=BeroNet BN4S0
location=PCI Bus 03 Slot 04
basechan=7
totchans=3
irq=0
type=digital-NT
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=B8ZS,AMI,HDB3
framing_opts=ESF,D4,CCS,CRC4
coding=AMI
framing=CCS
[4]
active=yes
alarms=OK
description=B4XXP (PCI) Card 0 Span 4
name=B4/0/4
manufacturer=Digium
devicetype=BeroNet BN4S0
location=PCI Bus 03 Slot 04
basechan=10
totchans=3
irq=0
type=digital-NT
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=B8ZS,AMI,HDB3
framing_opts=ESF,D4,CCS,CRC4
coding=AMI
framing=CCS
[5]
active=yes
alarms=OK
description=Wildcard TDM400P REV E/F Board 5
name=WCTDM/4
manufacturer=Digium
devicetype=Wildcard TDM400P REV E/F
location=PCI Bus 03 Slot 03
basechan=13
totchans=4
irq=0
type=analog
port=13,FXS
port=14,FXS
port=15,FXS
port=16,FXS
[6]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].1: BRI_NT
name=XBUS-00/XPD-00
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=17
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[7]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].2: BRI_NT
name=XBUS-00/XPD-01
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=20
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[8]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].3: BRI_TE
name=XBUS-00/XPD-02
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=23
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[9]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].4: BRI_TE
name=XBUS-00/XPD-03
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=26
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[10]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].5: BRI_TE
name=XBUS-00/XPD-04
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=29
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[11]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].6: BRI_TE
name=XBUS-00/XPD-05
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=32
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[12]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].7: BRI_TE
name=XBUS-00/XPD-06
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=35
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
[13]
active=yes
alarms=OK
description=Xorcom XPD [usb:X1037749].8: BRI_TE
name=XBUS-00/XPD-07
manufacturer=Xorcom Inc.
devicetype=Astribank2
location=usb-0000:00:13.5-3
basechan=38
totchans=3
irq=0
type=digital-BRI
syncsrc=0
lbo=0 db (CSU)/0-133 feet (DSX-1)
coding_opts=AMI
framing_opts=CCS
coding=AMI
framing=CCS
"""
    if len (sys.argv) == 2 and sys.argv [1] == 'test' :
        lcr_init (parsestring = lcr_output)
        DAHDI_Ports (parsestring = dahdi_output)
        for n, p in sorted (ISDN_Port.by_portnumber.iteritems ()) :
            print n, p
            print p.channel
    else :
        p = ISDN_Ports ()
        for port in p :
            print port
