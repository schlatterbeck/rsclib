#!/usr/bin/python
# Copyright (C) 2008 Dr. Ralf Schlatterbeck Open Source Consulting.
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

import asterisk.manager
from time               import sleep
from rsclib.Config_File import Config_File

class Config (Config_File) :
    def __init__ (self, config = 'autocaller', path = '/etc/autocaller') :
        self.__super.__init__ \
            ( path, config
            , ASTERISK_HOST         = 'localhost'
            , ASTERISK_MGR_ACCOUNT  = 'user'
            , ASTERISK_MGR_PASSWORD = 'secret'
            )
    # end def __init__
# end class Config

class Call (object) :
    def __init__ (self, call_manager, id) :
        self.manager = call_manager
        self.id      = id
        self.result  = None
    # end def __init__
# end class Call

class Call_Manager (object) :
    def __init__ (self) :
        self.config  = cfg = Config ()
        self.manager = mgr = asterisk.manager.Manager ()
        self.calls   = {}
        mgr.connect (cfg.ASTERISK_HOST)
        mgr.login   (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
        mgr.register_event ('*', self.handler)
    # end def __init__

    def handler (self, event, manager) :
        print "Received event: %s" % event.name
        for k in event.__dict__.iterkeys () :
            print "%s:" % k,
            if k != 'message' :
                print getattr (event, k)
    # end def handler

    def close (self) :
        if self.manager :
            self.manager.close  ()
            self.manager = None
    # end def close

    __del__ = close

    def __getattr__ (self, name) :
        if self.manager and not name.startswith ('__') :
            result = getattr (self.manager, name)
            setattr (self, name, result)
            return result
        raise AttributeError, name
    # end def __getattr__

    def originate (self, *args, **kw) :
        result = self.manager.originate (*args, **kw)
        id = result.headers ['Uniqueid']
        self.calls [id] = Call (self, id)
        print "Originate:", result.__dict__
        return result
    # end def originate
# end class Call_Manager

if __name__ == "__main__" :
    cm = Call_Manager ()
    response = cm.status ()
    print response
    #MaxRetries: 0
    #RetryTime: 60
    #WaitTime: 30
    vars = \
        { 'TUNE'     : 'Wohnung'
        , 'WAITTIME' : '1'
        }
    result = cm.originate ('Local/*16@intern', '1', 'ansage', 1, variables=vars)
    sleep (60)
    cm.close ()