#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2015 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from asterisk.manager   import Manager
from rsclib.execute     import Log
from rsclib.Config_File import Config_File

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

class Asterisk_Probe (Log) :

    def __init__ \
        ( self
        , config  = 'ast_isdn'
        , cfgpath = '/etc/ast_isdn'
        , cfg     = None
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
            mgr.connect (cfg.ASTERISK_HOST)
            mgr.login   (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
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

# end class Asterisk_Probe

if __name__ == '__main__' :
    ap = Asterisk_Probe ()
    d = ap.probe_apps ()
    for k, v in d.iteritems () :
        print "%s: %s" % (k, v)
    ap.close ()
