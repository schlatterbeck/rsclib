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
from Queue              import Queue, Empty
from time               import sleep
from rsclib.Config_File import Config_File

def call_id (uniqid) :
    """ Strip the last component off a Uniqueid, this apparently
        identifies all the call legs belonging to an asterisk call.
    """
    return '.'.join (uniqid.split ('.') [:-1])
# end def call_id

class Config (Config_File) :
    def __init__ (self, config = 'autocaller', path = '/etc/autocaller') :
        self.__super.__init__ \
            ( path, config
            , ASTERISK_HOST         = 'localhost'
            , ASTERISK_MGR_ACCOUNT  = 'user'
            , ASTERISK_MGR_PASSWORD = 'secret'
            , CALL_DELAY            = '1'
            , SOUND                 = 'abandon-all-hope'
            , CALLER_ID             = '16'
            , CALL_EXTENSION        = '1'
            , CALL_CONTEXT          = 'ansage'
            , CALL_PRIORITY         = '1'
            , CHANNEL_TYPE          = 'Local'
            , CHANNEL_SUFFIX        = '@dialout'
            )
    # end def __init__
# end class Config

class Call (object) :
    def __init__ (self, call_manager, callid) :
        self.manager    = call_manager
        self.callid     = callid
        self.events     = []
        self.uids       = {}
        self.causecode  = 0
        self.causetext  = ''
        self.dialstatus = ''
    # end def __init__

    def append (self, event) :
        id = event.headers ['Uniqueid']
        if event.name == 'Hangup' :
            del self.uids [id]
            if not self.causecode :
                self.causecode = int (event.headers ['Cause'])
                self.causetext = event.headers ['Cause-txt']
        else :
            self.uids [id] = True
            # Convention: Allow to retrieve dialstatus
            if event.name == 'Newexten' :
                app  = event.headers ['Application']
                data = event.headers ['AppData']
                if app == 'NoOp' and data.startswith ('Dialstatus:') :
                    self.dialstatus = data.split (':') [1].strip ()
        self.events.append (event)
    # end def append

    def __nonzero__ (self) :
        return bool (self.uids)
    # end def __nonzero__
# end class Call

class Call_Manager (object) :
    """ Simple call manager for asterisk.
        By default it's suggested you use something like the following
        in the dialplan::
         
         [ansage]
         exten => 1,1,Noop(ansage)
         exten => 1,n,Wait(${CALL_DELAY})
         exten => 1,n,GotoIf($["${SOUND}" = ""]?goodbye)
         exten => 1,n,Playback(${SOUND})
         exten => 1,n(goodbye),Hangup()

        and you're dialling out using a dialout context in your local
        dialplan.
    """

    def __init__ (self) :
        self.cfg            = cfg = Config ()
        self.manager        = mgr = asterisk.manager.Manager ()
        self.open_calls     = {}
        self.closed_calls   = {}
        self.queue          = Queue ()
        self.call_by_number = {}
        mgr.connect (cfg.ASTERISK_HOST)
        mgr.login   (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
        mgr.register_event ('*', self.handler)
    # end def __init__

    def handler (self, event, manager) :
        if 'Uniqueid' in event.headers :
            self.queue.put (event)
    # end def handler

    def queue_handler (self, timeout = None) :
        while self.open_calls :
            try :
                event = self.queue.get (timeout = timeout)
            except Empty :
                return
            if 'Uniqueid' in event.headers :
                uniqueid = event.headers ['Uniqueid']
                callid   = call_id (uniqueid)
                if callid in self.open_calls :
                    call = self.open_calls [callid]
                    call.append (event)
                    if not call :
                        self.closed_calls [callid] = call
                        del self.open_calls [callid]
                elif uniqueid != '<null>' :
                    pass
                    #print "oops:", callid, event.headers
            # print "Received event: %s" % event.name
    # end def queue_handler

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
        #print "Originate:", result.__dict__
        callid = call_id (result.headers ['Uniqueid'])
        self.open_calls [callid] = Call (self, callid)
        return callid
    # end def originate

    def call (self, number, timeout = None) :
        """ Originate a call using parameters from configuration.
        """
        vars = \
            { 'SOUND'      : self.cfg.SOUND
            , 'CALL_DELAY' : self.cfg.CALL_DELAY
            }
        channel = \
            '%s/%s%s' % (self.cfg.CHANNEL_TYPE, number, self.cfg.CHANNEL_SUFFIX)
        callid  = self.originate \
            ( channel   = channel
            , exten     = self.cfg.CALL_EXTENSION
            , context   = self.cfg.CALL_CONTEXT
            , priority  = self.cfg.CALL_PRIORITY
            , caller_id = self.cfg.CALLER_ID
            , async     = True
            , variables = vars
            )
        self.call_by_number [callid] = number
        self.queue_handler (timeout)
        return self.closed_calls [callid]
    # end def call
# end class Call_Manager

if __name__ == "__main__" :
    import sys
    number = sys.argv [1]
    cm = Call_Manager ()
    cm.call (number)
    for k, v in cm.closed_calls.iteritems () :
        print "Call: %s: %s (%s)" % (k, v.causetext, v.dialstatus)
        for event in v.events :
            print "  Event: %s" % event.name
            for ek, ev in event.headers.iteritems () :
                print "    %s: %s" % (ek, ev)
    cm.close ()
