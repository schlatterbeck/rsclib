#!/usr/bin/python
# Copyright (C) 2008-9 Dr. Ralf Schlatterbeck Open Source Consulting.
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
        But sometimes we get ids like asterisk-18477-1236970792
        while the allocated channel sometimes has asterisk-1236970792
        so we strip out the middle part.
        >>> call_id ('asterisk-18477-1236970792.47')
        'asterisk-1236970792'
        >>> call_id ('asterisk-1236970792.47')
        'asterisk-1236970792'
    """
    l = '.'.join (uniqid.split ('.') [:-1]).split ('-')
    return '-'.join ((l [0], l [-1]))
# end def call_id

class Config (Config_File) :
    def __init__ (self, config = 'autocaller', path = '/etc/autocaller') :
        self.__super.__init__ \
            ( path, config
            , MATCH_CHANNEL         = False
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
    """
    >>> class Manager :
    ...     def register (*args, **kw) :
    ...         print "register"
    >>>
    >>> class Event :
    ...     def __init__ (self, d) :
    ...         self.name = d ['Event']
    ...         self.headers = d
    >>>
    >>> m = Manager()
    >>> c = Call (m, '4711', 'asterisk-2633-1243166465.17142')
    register
    >>> e = Event ({'Uniqueid': 'asterisk-1243166465.17141'
    ...           , 'Privilege': 'call,all'
    ...           , 'Event': 'Newchannel'
    ...           , 'Channel': 'lcr/12284'})
    >>> c.append (e)
    >>> bool (c)
    True
    >>> c = Call (m, '4712', 'asterisk-2633-1243303265.18231')
    register
    >>> e = Event ({'AppData': '', 'Extension': 'h'
    ...           , 'Uniqueid': 'asterisk-1243303265.18230', 'Priority': '5'
    ...           , 'Application': 'NoOp', 'Context': 'attendo'
    ...           , 'Privilege': 'call,all', 'Event': 'Newexten'
    ...           , 'Channel': 'lcr/13071'})
    >>> c.append (e)
    >>> bool (c)
    True
    """

    def __init__ \
        ( self
        , call_manager
        , actionid
        , uniqueid  = None
        , caller_id = None
        , context   = None
        ) :
        self.manager          = call_manager
        self.actionid         = actionid
        self.uniqueid         = None
        self.caller_id        = caller_id
        self.context          = context
        self.callid           = None
        self.min_seqno        = None
        self.events           = []
        self.uids             = {}
        self.uids_seen        = False
        self.state_by_chan    = {}
        self.context_by_chan  = {}
        self.callerid_by_chan = {}
        self.causecode        = 0
        self.causetext        = ''
        self.seqno_seen       = None
        # If we're sure about our whole uniqueid (OriginateResponse seen)
        self.sure             = False
        self.dialstatus       = ''
        if uniqueid is not None :
            self._set_id (uniqueid)
    # end def __init__

    def append (self, event) :
        assert (self.uniqueid)
        self.event = event
        self.id    = event.headers ['Uniqueid']
        self.events.append (event)
        # ignore calls in progress with lower seqno
        if self.seqno < self.min_seqno :
            return
        self.uids [self.id] = True
        self.uids_seen      = True
        handler = getattr (self, 'handle_%s' % event.name, None)
        if handler :
            handler ()
    # end def append

    def handle_context (self) :
        chan = self.event.headers ['Channel']
        if chan not in self.context_by_chan :
            self.context_by_chan [chan] = {}
        self.context_by_chan [chan][self.event.headers ['Context']] = True
    # end def handle_context

    def handle_Hangup (self) :
        del self.uids [self.id]
        chan  = self.event.headers ['Channel']
        # ignore name-clash with incoming call:
        if chan in self.state_by_chan and 'Ring' in self.state_by_chan [chan] :
            return
        # ignore channel without our caller-id
        if  (   self.caller_id
            and chan in self.callerid_by_chan
            and self.caller_id not in self.callerid_by_chan [chan]
            ) :
            return
        # ignore channel with context but without our context
        if  (   self.context
            and chan in self.context_by_chan
            and self.context not in self.context_by_chan [chan]
            ) :
            return
        # when we know our unique id (and the seqno is the last part of
        # it) we don't accept hangup cause for other seqno:
        if self.sure and self.seqno != self.seqno_seen :
            return
        if not self.causecode or self.seqno <= self.seqno_seen :
            self.causecode  = int (self.event.headers ['Cause'])
            self.causetext  = self.event.headers ['Cause-txt']
            self.seqno_seen = self.seqno
    # end def handle_Hangup

    def handle_Newcallerid (self) :
        callerid = self.event.headers ['CallerID']
        if callerid == '<Unknown>' :
            return
        chan = self.event.headers ['Channel']
        if chan not in self.callerid_by_chan :
            self.callerid_by_chan [chan] = {}
        self.callerid_by_chan [chan][callerid] = True
    # end def handle_Newcallerid

    def handle_Newexten (self) :
        # Convention: Allow to retrieve dialstatus
        app  = self.event.headers ['Application']
        data = self.event.headers ['AppData']
        if app == 'NoOp' and data.startswith ('Dialstatus:') :
            self.dialstatus = data.split (':') [1].strip ()
        self.handle_context ()
    # end def handle_Newexten

    def handle_Newstate (self) :
        chan = self.event.headers ['Channel']
        if chan not in self.state_by_chan :
            self.state_by_chan [chan] = {}
        self.state_by_chan [chan][self.event.headers ['State']] = True
    # end def handle_Newstate

    def handle_OriginateResponse (self) :
        if self.actionid != self.event.headers ['ActionID'] :
            return
        if self.seqno_seen :
            if self.seqno == self.seqno_seen :
                self.sure = True
            else :
                self.sure = None
        else :
            self.seqno_seen = self.seqno
            self.sure       = True
        self.handle_context ()
    # end def handle_OriginateResponse

    @property
    def seqno (self) :
        return int (self.id.rsplit ('.', 1) [1])
    # end def seqno

    def _set_id (self, uniqueid) :
        self.uniqueid = self.id = uniqueid
        callid = call_id (self.uniqueid)
        if self.callid :
            assert (callid == self.callid)
        if self.min_seqno is None :
            self.min_seqno = self.seqno
        self.callid = callid
        self.manager.register (self)
    # end def _set_id

    def set_id (self, event) :
        actionid = event.headers.get ('ActionID')
        assert (not actionid or actionid == self.actionid)
        uniqueid = event.headers ['Uniqueid']
        self._set_id (uniqueid)
    # end def set_id

    def __nonzero__ (self) :
        return bool (not self.uids_seen or self.uids)
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

    def __init__ (self, config = 'autocaller', cfgpath = '/etc/autocaller') :
        self.cfg            = cfg = Config (config = config, path = cfgpath)
        self.manager        = mgr = asterisk.manager.Manager ()
        self.open_calls     = {} # by actionid
        self.open_by_id     = {} # by callid (part of uniqueid)
        self.open_by_chan   = {} # by channel
        self.closed_calls   = {} # by actionid
        self.queue          = Queue ()
        self.call_by_number = {}
        self.unhandled      = []
        mgr.connect (cfg.ASTERISK_HOST)
        mgr.login   (cfg.ASTERISK_MGR_ACCOUNT, cfg.ASTERISK_MGR_PASSWORD)
        mgr.register_event ('*', self.handler)
    # end def __init__

    def call \
        ( self
        , number
        , timeout        = None
        , call_delay     = None
        , sound          = None
        , channel_type   = None
        , channel_suffix = None
        , call_extension = None
        , call_context   = None
        , call_priority  = None
        , caller_id      = None
        ) :
        """ Originate a call using parameters from configuration.
            Parameter override is possible via call parameters.
            The timeout is used for the queue_handler timeout. The
            call_delay is passed as a "DELAY" variable to asterisk for
            use in the dialplan. Same for sound passed as variable
            "SOUND". The channel variables (and the number) are used for
            constructing the asterisk channel. The call parameters are
            used for specifying the dialplan destination after a
            successful call. The caller_id the caller id for the call.
        """
        vars = \
            { 'SOUND'      : sound      or self.cfg.SOUND
            , 'CALL_DELAY' : call_delay or self.cfg.CALL_DELAY
            }
        type    = channel_type
        if type is None :
            type = self.cfg.CHANNEL_TYPE
        suffix  = channel_suffix
        if suffix is None :
            suffix = self.cfg.CHANNEL_SUFFIX
        actionid  = self.originate \
            ( self.cfg.MATCH_CHANNEL
            , channel   = '%s/%s%s' % (type, number, suffix)
            , exten     = call_extension or self.cfg.CALL_EXTENSION
            , context   = call_context   or self.cfg.CALL_CONTEXT
            , priority  = call_priority  or self.cfg.CALL_PRIORITY
            , caller_id = caller_id      or self.cfg.CALLER_ID
            , async     = True
            , variables = vars
            )
        self.call_by_number [actionid] = number
        # maybe call already terminated or we have a permission problem:
        if actionid not in self.closed_calls :
            self.queue_handler (timeout)
        try :
            return self.closed_calls [actionid]
        except KeyError :
            pass
        return None
    # end def call

    def close (self) :
        if self.manager :
            self.manager.close  ()
            self.manager = None
    # end def close

    def handler (self, event, manager) :
        if 'Uniqueid' in event.headers :
            self.queue.put (event)
    # end def handler

    def originate (self, match_channel = False, *args, **kw) :
        """ Originate a call with the given asterisk call parameters.
            If match_channel we try fuzzy-matching on the called channel
            name when trying to determine the open call. This is needed
            with asterisk 1.2 since 1.2 doesn't return the unique id.
        """
        result = self.manager.originate (*args, **kw)
        #print "Originate:", result.__dict__
        actionid = result.headers ['ActionID']
        uniqueid = result.headers.get ('Uniqueid')
        call = Call \
            ( self
            , actionid
            , uniqueid
            , caller_id = kw.get ('caller_id')
            , context   = kw.get ('context')
            )
        if result.headers.get ('Response') == 'Error' :
            call.causetext = result.headers.get ('Message') or 'Unknown error'
            call.causecode = -1
            self.closed_calls [actionid] = call
        else :
            self.open_calls [actionid] = call
            if match_channel :
                self.open_by_chan [kw ['channel']] = call
        return actionid
    # end def originate

    def queue_handler (self, timeout = None) :
        while self.open_calls :
            try :
                event = self.queue.get (timeout = timeout)
            except Empty :
                return
            #print "Received event: %s" % event.name, event.headers
            assert ('Uniqueid' in event.headers)
            uniqueid = event.headers ['Uniqueid']
            # ignore bogus uniqueid in asterisk 1.4
            if uniqueid == '<null>' :
                continue
            callid   = call_id (uniqueid)
            channel  = event.headers.get ('Channel')
            if channel :
                channel = '-'.join (channel.split ('-') [:-1])
            if channel in self.open_by_chan :
                call = self.open_by_chan [channel]
                del self.open_by_chan [channel]
                call.set_id (event)
            if callid in self.open_by_id :
                self._handle_queued_event (event)
            else :
                self.unhandled.append (event)
                actionid = event.headers.get ('ActionID')
                if actionid and actionid in self.open_calls :
                    call = self.open_calls [actionid]
                    call.set_id (event)
                    new_unhandled = []
                    for e in self.unhandled :
                        if not self._handle_queued_event (e) :
                            new_unhandled.append (e)
                    self.unhandled = new_unhandled
    # end def queue_handler

    def register (self, call) :
        """ Called when one of our calls knows its callid. """
        assert (call.callid not in self.open_by_id)
        self.open_by_id [call.callid] = call
    # end def register

    __del__ = close

    def __getattr__ (self, name) :
        if self.manager and not name.startswith ('__') :
            result = getattr (self.manager, name)
            setattr (self, name, result)
            return result
        raise AttributeError, name
    # end def __getattr__

    def _handle_queued_event (self, event) :
        """ Try handling the event. Returns True on success False
            otherwise.
        """
        #print "Handling event: %s" % event.name, event.headers
        uniqueid = event.headers ['Uniqueid']
        callid   = call_id (uniqueid)
        if callid in self.open_by_id :
            call = self.open_by_id [callid]
            call.append (event)
            if not call :
                actionid = call.actionid
                self.closed_calls [actionid] = call
                del self.open_calls [actionid]
                del self.open_by_id [callid]
            return True
        elif uniqueid != '<null>' :
            pass
        return False
    # end def _handle_queued_event

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
