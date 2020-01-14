#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2015-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__         import print_function
from time               import sleep
from asterisk.manager   import Manager, ManagerSocketException
from rsclib.execute     import Log
from rsclib.Config_File import Config_File

class Config (Config_File) :

    def __init__ (self, config = 'ast_probe', path = '/etc/ast_probe') :
        self.__super.__init__ \
            ( path, config
            , ASTERISK_HOST         = 'localhost'
            , ASTERISK_MGR_ACCOUNT  = 'user'
            , ASTERISK_MGR_PASSWORD = 'secret'
            )
    # end def __init__

# end class Config

class Asterisk_Probe (Log) :

    def __init__ \
        ( self
        , config  = 'ast_probe'
        , cfgpath = '/etc/ast_probe'
        , cfg     = None
        , retries = 0
        , ** kw
        ) :
        if cfg :
            self.cfg = cfg
        else :
            self.cfg = cfg = Config (config = config, path = cfgpath)
        self.__super.__init__ (** kw)
        if 'manager' in kw :
            self.mgr = mgr = kw ['manager']
        else :
            self.mgr = mgr = Manager ()
            for r in range (retries + 1) :
                try :
                    mgr.connect (cfg.ASTERISK_HOST)
                    break
                except ManagerSocketException :
                    if r >= retries :
                        raise
                    sleep (1)
            mgr.login (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
    # end def __init__

    def close (self) :
        self.mgr.close ()
        self.mgr = None
    # end def close

    def probe_apps (self) :
        mgr = self.mgr
        r = mgr.command ('core show applications')
        d = {}
        for line in r.data.split ('\n') :
            line = line.strip ()
            try :
                k, v = (x.strip () for x in line.split (':', 1))
            except ValueError :
                assert (  not line
                       or line == '--END COMMAND--'
                       or line.startswith ('-=') and line.endswith ('=-')
                       )
                continue
            d [k] = v
        return d
    # end def probe_apps

    def probe_sip_registry (self) :
        r = self.mgr.command ('sip show registry')
        d = {}
        for line in r.data.split ('\n') :
            data = line.split (None, 5)
            if len (data) != 6 :
                assert data == [] or data [1] == 'SIP' or data [0] == '--END'
                continue
            if data [0] == 'Host' :
                continue
            if data [4] == 'Request' and data [5].startswith ('Sent') :
                data [4] = 'Request Sent'
                data [5] = data [5].split (None, 1) [-1]
            host, port = data [0].split (':', 1)
            d [host] = data [4]
        return d
    # end def probe_sip_registry

    def reload_sip (self) :
        r = self.mgr.command ('sip reload')
        self.log.info ('SIP reload')
    # end def reload_sip

# end class Asterisk_Probe

if __name__ == '__main__' :
    ap = Asterisk_Probe ()
    d = ap.probe_apps ()
    for k in d :
        v = d [k]
        print ("%s: %s" % (k, v))
    ap.close ()
