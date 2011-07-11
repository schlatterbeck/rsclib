#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009 Dr. Ralf Schlatterbeck Open Source Consulting.
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
from rsclib.execute     import Exec, Exec_Error

class LCR_Port (autosuper) :
    """ Represent an ISDN Port of Linux Call Router
    """
    by_portnumber = {}
    def __init__ \
        ( self
        , number
        , name      = None
        , interface = None
        , status    = None
        , mode      = None
        , l1        = None 
        , l2        = None
        , usage     = None
        ) :
        self.number    = number
        # register:
        self.by_portnumber [number] = self
        self.name      = name
        self.interface = interface
        self.status    = status
        self.mode      = mode
        self.l1        = l1
        self.l2        = l2
        self.usage     = usage
    # end def __init__

    def __str__ (self) :
        return ', '.join \
            ("%s = %s" % (k, repr (v))
             for k, v in sorted (self.__dict__.iteritems ())
             if k [0] != '_'
            )
    # end def __str__
    
    def __repr__ (self) :
        return "%s (%s)" % (self.__class__.__name__, str (self))
# end class LCR_Port


class LCR_Ports (Parser, Exec) :
    """ Represent all ISDN ports of Linux Call Router
        Parse the output of "lcradmin portinfo" and put the result into
        a nice data structure. For parsing we use the stateparser from
        rsclib.
    """

    re_empty = re.compile (r"^$")
    re_start = re.compile (r"^([0-9-a-zA-Z]+):\s*$")
    re_param = re.compile (r"\s+([-a-z0-9 ]*[a-zA-Z0-9])\s+=\s+(.*)$")
    re_port  = re.compile (r'^([0-9]+)\s+"([^"]+)"')

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

    def __init__ (self, parsestring = None, **kw) :
        self.__super.__init__ (**kw)
        self.interface = None
        self.port      = None
        if parsestring :
            parsestring = parsestring.split ('\n')
        else :
            parsestring = self.exec_pipe (("lcradmin", "portinfo"))
        self.parse (parsestring)
    # end def __init__

    def port_start (self, state, new_state, match) :
        self.interface = match.groups () [0].strip ()
        self.port      = None
        self.push (state, new_state, match)
    # end def port_start

    def port_set (self, state, new_state, match) :
        name, value = match.groups ()
        name = name.replace ('-', '_')
        name = self.attrs.get (name, name)
        if name == 'port' :
            m = self.re_port.match (value)
            number, name     = m.groups ()
            number = int (number)
            self.port = LCR_Port (number, name, interface = self.interface)
        elif name == 'usage' :
            self.port.usage = int (value)
        elif name :
            setattr (self.port, name, value)
    # end def port_set
# end class LCR_Ports

def lcr_init (**kw) :
    """ Parse once """
    try :
        LCR_Ports (**kw)
    except Exec_Error :
        pass
# end def lcr_init

if __name__ == '__main__' :
    output = """
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
    lcr_init (parsestring = output)
    print LCR_Port.by_portnumber
