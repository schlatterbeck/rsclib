#!/usr/bin/python
# Copyright (C) 2008-15 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__ import print_function

import asterisk.manager
from sys                import stderr
from Queue              import Queue, Empty
from time               import sleep
from random             import randint
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
        >>> call_id ('1371796712.69')
        '1371796712'
        >>> call_id ('<null>')
        ''
    """
    if uniqid == '<null>' :
        return ''
    l = '.'.join (uniqid.split ('.') [:-1]).split ('-')
    if len (l) == 1 :
        return l [0]
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
            , ASTERISK_PORT         = 5038
            , CALL_DELAY            = '1'
            , SOUND                 = 'abandon-all-hope'
            , CALLER_ID             = '16'
            , CALL_EXTENSION        = '1'
            , CALL_CONTEXT          = 'ansage'
            , CALL_PRIORITY         = '1'
            , CHANNEL_TYPE          = 'Local'
            , CHANNEL_SUFFIX        = '@dialout'
            , ACCOUNT_CODE          = 'RANDOMID'
            )
    # end def __init__
# end class Config

class Call (object) :
    """
    A note on the account (account-code in asterisk) parameter: This
    asumes that we generate a unique account code using the RANDOMID
    feature of Call_Manager.
    >>> class Mock_Manager :
    ...     def register (*args, **kw) :
    ...         print ("register")
    >>>
    >>> from asterisk.astemu import AsteriskEmu, Event
    >>>
    >>> m = Mock_Manager ()
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
    >>> m = Mock_Manager ()
    >>> c = Call (m, '00000007','1333330442.4619','','linecheck','1588267611')
    register
    >>> e1 = Event ({'AccountCode': '', 'Uniqueid': '1333330442.4619'
    ...            , 'ChannelState': '1', 'Exten': '', 'CallerIDNum': ''
    ...            , 'Context': '', 'CallerIDName': '', 'Privilege': 'call,all'
    ...            , 'Event': 'Newchannel', 'Channel': 'lcr/4590'
    ...            , 'ChannelStateDesc': 'Rsrvd'
    ...            })
    >>> c.append (e1)
    >>> e2 = Event ({'AccountCode': '1588267611', 'OldAccountCode': ''
    ...            , 'Uniqueid': '1333330442.4619', 'Privilege': 'call,all'
    ...            , 'Event': 'NewAccountCode', 'Channel': 'lcr/4590'
    ...            })
    >>> c.append (e2)
    >>> e3 = Event ({'CallerIDNum': '', 'Uniqueid': '1333330442.4619'
    ...            , 'CallerIDName': '', 'Privilege': 'call,all'
    ...            , 'CID-CallingPres': '0 (Presentation Allowed, Not Screened)'
    ...            , 'Event': 'NewCallerid', 'Channel': 'lcr/4590'
    ...            })
    >>> c.append (e3)
    >>> e4 = Event ({'AccountCode': '', 'Uniqueid': '1333330442.4620'
    ...            , 'ChannelState': '1', 'Exten': '', 'CallerIDNum': ''
    ...            , 'Context': '', 'CallerIDName': '', 'Privilege': 'call,all'
    ...            , 'Event': 'Newchannel', 'Channel': 'lcr/4591'
    ...            , 'ChannelStateDesc': 'Rsrvd'
    ...            })
    >>> c.append (e4)
    >>> e5 = Event ({'ChannelState': '4', 'CallerIDNum': '0000000000'
    ...            , 'Uniqueid': '1333330442.4620', 'CallerIDName': ''
    ...            , 'Privilege': 'call,all', 'Event': 'Newstate'
    ...            , 'Channel': 'lcr/4591', 'ChannelStateDesc': 'Ring'
    ...            })
    >>> c.append (e5)
    >>> e6 = Event ({'ChannelState': '7', 'CallerIDNum': '0000000000'
    ...            , 'Uniqueid': '1333330442.4620', 'CallerIDName': ''
    ...            , 'Privilege': 'call,all', 'Event': 'Newstate'
    ...            , 'Channel': 'lcr/4591', 'ChannelStateDesc': 'Busy'
    ...            })
    >>> c.append (e6)
    >>> e7 = Event ({'AccountCode': '', 'Uniqueid': '1333330442.4621'
    ...            , 'ChannelState': '1', 'Exten': '', 'CallerIDNum': ''
    ...            , 'Context': '', 'CallerIDName': '', 'Privilege': 'call,all'
    ...            , 'Event': 'Newchannel', 'Channel': 'lcr/4592'
    ...            , 'ChannelStateDesc': 'Rsrvd'
    ...            })
    >>> c.append (e7)
    >>> e8 = Event ({'ChannelState': '4', 'CallerIDNum': '0332243116'
    ...            , 'Uniqueid': '1333330442.4621', 'CallerIDName': ''
    ...            , 'Privilege': 'call,all', 'Event': 'Newstate'
    ...            , 'Channel': 'lcr/4592', 'ChannelStateDesc': 'Ring'
    ...            })
    >>> c.append (e8)
    >>> e9 = Event ({'Cause-txt': 'Normal Clearing'
    ...            , 'CallerIDNum': '0000000000', 'Uniqueid': '1333330442.4620'
    ...            , 'CallerIDName': '<unknown>', 'Privilege': 'call,all'
    ...            , 'Cause': '16', 'Event': 'Hangup', 'Channel': 'lcr/4591'
    ...            })
    >>> c.append (e9)
    >>> eA = Event ({'ChannelState': '6', 'CallerIDNum': '0332243116'
    ...            , 'Uniqueid': '1333330442.4621', 'CallerIDName': ''
    ...            , 'Privilege': 'call,all', 'Event': 'Newstate'
    ...            , 'Channel': 'lcr/4592', 'ChannelStateDesc': 'Up'
    ...            })
    >>> c.append (eA)
    >>> eB = Event ({'Privilege': 'call,all', 'Event': 'MonitorStart'
    ...            , 'Channel': 'lcr/4592', 'Uniqueid': '1333330442.4621'
    ...            })
    >>> c.append (eB)
    >>> eC = Event ({'Cause-txt': 'User busy', 'CallerIDNum': '<unknown>'
    ...            , 'Uniqueid': '1333330442.4619', 'CallerIDName': '<unknown>'
    ...            , 'Privilege': 'call,all', 'Cause': '17', 'Event': 'Hangup'
    ...            , 'Channel': 'lcr/4590'
    ...            })
    >>> c.append (eC)
    >>> eD = Event (dict ( Event = 'OriginateResponse', Privilege = 'call,all'
    ...                  , ActionID = 'ruf1lszsrv-00000007'
    ...                  , Response = 'Failure'
    ...                  , Channel = 'LCR/Ext1/0000000000'
    ...                  , Context = 'linecheck'
    ...                  , Exten = '1'
    ...                  , Reason = '1'
    ...                  , Uniqueid = '<null>'
    ...                  , CallerIDNum = '<unknown>'
    ...                  , CallerIDName = '<unknown>'
    ...                  ))
    >>> c.append (eD)
    >>> bool (c)
    False
    >>> c.reason
    -1
    >>> m = Mock_Manager ()
    >>> c = Call (m, '00000007', '1333330442.4619', '', 'linecheck')
    register
    >>> c.append (e1)
    >>> c.append (e2)
    >>> c.append (e3)
    >>> c.append (e4)
    >>> c.append (e5)
    >>> c.append (e6)
    >>> c.append (e7)
    >>> c.append (e8)
    >>> c.append (e9)
    >>> c.append (eA)
    >>> c.append (eB)
    >>> c.append (eC)
    >>> c.append (eD)
    >>> bool (c)
    True
    >>> c = Call (m, '00000007', '1333330442.4619', '', 'linecheck')
    register
    >>> c.append (e1)
    >>> c.append (e2)
    >>> c.append (e3)
    >>> c.append (e4)
    >>> c.append (e5)
    >>> c.append (e6)
    >>> c.append (e9)
    >>> c.append (eC)
    >>> c.append (eD)
    >>> bool (c)
    False
    >>> c = Call ( m, 'asterisk04-7950-00000002'
    ...          , 'a.2', context = 'active_linecheck')
    register
    >>> e = Event ({'Event': 'OriginateResponse'
    ...           , 'Privilege': 'call,all'
    ...           , 'ActionID': 'asterisk04-7950-00000002'
    ...           , 'Response': 'Failure'
    ...           , 'Channel': 'dahdi/7/0732731469'
    ...           , 'Context': 'active_linecheck'
    ...           , 'Exten': '1'
    ...           , 'Reason': '5'
    ...           , 'Uniqueid': '<null>'
    ...           , 'CallerIDNum': '<unknown>'
    ...           , 'CallerIDName': '<unknown>'
    ...           })
    >>> c.append (e)
    >>> c.sure
    False
    >>> bool (c)
    False
    >>> c.reason
    5
    >>> c.causecode
    17
    >>> c.causetext
    'Originate failed: local line busy'

    >>> queued = 'Originate successfully queued'
    >>> r = Event (Response = ('Success',), Message = (queued,))
    >>> d = dict (AsteriskEmu.default_events)
    >>> d.update (Originate = (r, e))
    >>> a = AsteriskEmu (d)
    >>> m = Call_Manager (host = 'localhost', port = a.port)
    >>> c = m.call ('4711', timeout = 1, channel_type = 'dahdi/1')
    >>> bool (c)
    False
    >>> c.causetext
    'Originate failed: local line busy'
    >>> c.causecode
    17
    >>> c.reason
    5
    >>> m.close ()
    >>> a.close ()

    >>> m = Mock_Manager ()
    >>> c = Call ( m, 'asterisk05-11626-00000002'
    ...          , 'a.2', context = 'active_linecheck')
    register
    >>> e = Event ({'Event': 'OriginateResponse'
    ...           , 'Privilege': 'call,all'
    ...           , 'ActionID': 'asterisk05-11626-00000002'
    ...           , 'Response': 'Success'
    ...           , 'Channel': 'DAHDI/i3/0732731469-2a'
    ...           , 'Context': 'active_linecheck'
    ...           , 'Exten': '1'
    ...           , 'Reason': '4'
    ...           , 'Uniqueid': '1371796712.69'
    ...           , 'CallerIDNum': '<unknown>'
    ...           , 'CallerIDName': '<unknown>'
    ...           })
    >>> c.append (e)
    >>> c.sure
    True
    >>> bool (c)
    True
    >>> c.reason
    4
    >>> h = Event ({'Event': 'Hangup'
    ...           , 'Privilege': 'call,all'
    ...           , 'Channel': 'DAHDI/i3/0732731469-2a'
    ...           , 'Uniqueid': '1371796712.69'
    ...           , 'CallerIDNum': '<unknown>'
    ...           , 'CallerIDName': '<unknown>'
    ...           , 'ConnectedLineNum': '<unknown>'
    ...           , 'ConnectedLineName': '<unknown>'
    ...           , 'Cause': '87'
    ...           , 'Cause-txt': 'Unknown'
    ...           })
    >>> c.append (h)
    >>> c.causecode
    87
    >>> c.causetext
    'Unknown'
    >>> bool (c)
    False
    >>> c.reason
    4

    # hangup after originate response
    >>> d = dict (AsteriskEmu.default_events)
    >>> d.update (Originate = (r, e, h))
    >>> a = AsteriskEmu (d)
    >>> ctx = 'active_linecheck'
    >>> m = Call_Manager (host = 'localhost', port = a.port)
    >>> c = m.call ('4711', 1, channel_type = 'dahdi/1', call_context = ctx)
    >>> bool (c)
    False
    >>> c.causetext
    'Unknown'
    >>> c.causecode
    87
    >>> c.reason
    4
    >>> m.close ()
    >>> a.close ()

    # hangup before originate response
    >>> d = dict (AsteriskEmu.default_events)
    >>> d.update (Originate = (r, h, e))
    >>> a = AsteriskEmu (d)
    >>> ctx = 'active_linecheck'
    >>> m = Call_Manager (host = 'localhost', port = a.port)
    >>> c = m.call ('4711', 1, channel_type = 'dahdi/1', call_context = ctx)
    >>> bool (c)
    False
    >>> c.causetext
    'Unknown'
    >>> c.causecode
    87
    >>> c.reason
    4
    >>> m.close ()
    >>> a.close ()

    >>> events = parse_events ('fail.log')
    >>> d = dict (AsteriskEmu.default_events)
    >>> d.update (Originate = events)
    >>> a = AsteriskEmu (d)
    >>> ctx = 'active_linecheck'
    >>> m = Call_Manager (host = 'localhost', port = a.port, match_account = 1)
    >>> par = dict (channel_type = 'dahdi/1', call_context = ctx)
    >>> par ['account'] = '2070625609'
    >>> c = m.call ('4711', 1, ** par)
    >>> bool (c)
    False
    >>> c.causetext
    'User busy'
    >>> c.causecode
    17
    >>> c.reason
    4
    >>> m.close ()
    >>> a.close ()
    """

    def __init__ \
        ( self
        , call_manager
        , actionid
        , uniqueid  = None
        , caller_id = None
        , context   = None
        , account   = None
        ) :
        self.manager          = call_manager
        self.actionid         = actionid
        self.uniqueid         = None
        self.caller_id        = caller_id
        self.context          = context
        self.account          = account
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
        self.reason           = -1
        self.seqno_seen       = None
        # If we're sure about our whole uniqueid (OriginateResponse seen)
        self.sure             = False
        self.fail             = False # for OriginateResponse Failure
        self.dialstatus       = ''
        if uniqueid is not None :
            self._set_id (uniqueid)
    # end def __init__

    def append (self, event) :
        self.event = event
        self.id    = event.headers ['Uniqueid']
        if self.id == '<null>' :
            if self.actionid != self.event.headers.get ('ActionID') :
                return
        self.events.append (event)
        # ignore calls in progress with lower seqno
        if self.seqno and self.seqno < self.min_seqno :
            return
        if self.id != '<null>' :
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

    def handle_NewAccountCode (self) :
        if not self.account :
            return
        account = self.event.headers.get ('AccountCode')
        if account == self.account :
            self.sure       = True
            self.uniqueid   = self.id
            self.seqno_seen = self.seqno
    # end def handleNewAccountCode

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
        for k in 'State', 'ChannelStateDesc', 'ChannelState' :
            if k in self.event.headers :
                self.state_by_chan [chan][self.event.headers [k]] = True
                break
    # end def handle_Newstate

    def handle_OriginateResponse (self) :
        #print ("OriginateResponse", file = stderr)
        if self.actionid != self.event.headers ['ActionID'] :
            return
        self.reason = int (self.event.headers.get ('Reason', -1))
        if self.seqno_seen :
            if self.seqno == self.seqno_seen :
                self.sure     = True
                self.uniqueid = self.id
            else :
                self.sure = None
        else :
            if self.seqno :
                self.seqno_seen = self.seqno
                self.uniqueid   = self.id
                self.sure       = True
            # If we see a fail response, make sure we don't look for
            # further events for this call
            if self.event.headers.get ('Response') == 'Failure' :
                self.fail = True
                if self.reason == 5 :
                    self.causetext = 'Originate failed: local line busy'
                    self.causecode = 17
                else :
                    self.causetext = 'Originate failed: %s' % self.reason
                    self.causecode = -1
        self.handle_context ()
    # end def handle_OriginateResponse

    @property
    def seqno (self) :
        if self.id == '<null>' :
            return None
        return int (self.id.rsplit ('.', 1) [1])
    # end def seqno

    def _set_id (self, uniqueid) :
        self.uniqueid = self.id = uniqueid
        callid = call_id (self.uniqueid)
        assert (callid)
        if self.callid :
            assert (callid == self.callid)
        self.callid = callid
        # Only register once
        if self.min_seqno is None :
            self.min_seqno = self.seqno
            self.manager.register (self)
    # end def _set_id

    def set_id (self, event) :
        actionid = event.headers.get ('ActionID')
        assert (not actionid or actionid == self.actionid)
        uniqueid = event.headers ['Uniqueid']
        assert (uniqueid != '<null>')
        self._set_id (uniqueid)
    # end def set_id

    def unregister (self) :
        """ Unregister this call from the manager (deleting it there).
            Save memory for long-running call-setup tasks
        """
        self.manager.unregister (self)
    # end def unregister

    def __nonzero__ (self) :
        """ Returns False when call finished or failed.
        """
        if self.fail :
            return False
        if not self.uids_seen :
            return True
        if self.sure :
            return self.uniqueid in self.uids
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

    def __init__ \
        ( self
        , config        = 'autocaller'
        , cfgpath       = '/etc/autocaller'
        , host          = None
        , port          = 5038
        , match_account = False
        , cfg           = None
        ) :
        if cfg :
            self.cfg = cfg
        else :
            self.cfg = cfg  = Config (config = config, path = cfgpath)
        self.manager        = mgr = asterisk.manager.Manager ()
        self.match_account  = match_account
        self.open_calls     = {} # by actionid
        self.open_by_id     = {} # by callid (part of uniqueid)
        self.open_by_chan   = {} # by channel
        self.open_by_acct   = {} # by account code
        self.closed_calls   = {} # by actionid
        self.queue          = Queue ()
        self.call_by_number = {}
        self.unhandled      = []
        mgr.connect (host or cfg.ASTERISK_HOST, port = port)
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
        , account        = '' # use cfg.ACCOUNT_CODE
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
            Special account code "RANDOMID" will place a (unique) random
            ID into the account-code for matching a call.
        """
        self.cleanup ()
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
        if account == '' :
            account = self.cfg.ACCOUNT_CODE
        actionid  = self.originate \
            ( self.cfg.MATCH_CHANNEL
            , channel   = '%s/%s%s' % (type, number, suffix)
            , exten     = call_extension or self.cfg.CALL_EXTENSION
            , context   = call_context   or self.cfg.CALL_CONTEXT
            , priority  = call_priority  or self.cfg.CALL_PRIORITY
            , caller_id = caller_id      or self.cfg.CALLER_ID
            , account   = account
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

    def cleanup (self) :
        """ Clean up unneeded data structures.
        """
        if not self.open_calls :
            if self.open_by_id :
                self.open_by_id   = {}
            if self.open_by_chan :
                self.open_by_chan = {}
            if self.open_by_acct :
                self.open_by_acct = {}
            self.unhandled = []
    # end def cleanup

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
            Special handling for account code: if it is RANDOMID we pass
            a unique value as action id for (fuzzy) matching.
        """
        random_account = False
        if 'account' in kw and kw ['account'] is None :
            del kw ['account']
        if kw.get ('account') == 'RANDOMID' :
            kw ['account'] = str (randint (0, 2 ** 32 - 1))
            random_account = True
        if 'account' in kw and self.match_account :
            random_account = True

        result = self.manager.originate (*args, **kw)
        #print ("Originate:", result.__dict__, file = stderr)
        actionid = result.headers ['ActionID']
        uniqueid = result.headers.get ('Uniqueid')
        call = Call \
            ( self
            , actionid
            , uniqueid
            , caller_id = kw.get ('caller_id')
            , context   = kw.get ('context')
            , account   = [None, kw.get ('account')] [random_account]
            )
        if result.headers.get ('Response') == 'Error' :
            call.causetext = result.headers.get ('Message') or 'Unknown error'
            call.causecode = -1
            self.closed_calls [actionid] = call
        else :
            self.open_calls [actionid] = call
            if match_channel :
                self.open_by_chan [kw ['channel']] = call
            if random_account :
                self.open_by_acct [kw ['account']] = call
        return actionid
    # end def originate

    def queue_handler (self, timeout = None) :
        while self.open_calls :
            try :
                event = self.queue.get (timeout = timeout)
            except Empty :
                return
            #print ("Received event: %s" % event.name, event.headers)
            assert ('Uniqueid' in event.headers)
            uniqueid = event.headers ['Uniqueid']
            callid   = call_id (uniqueid)
            channel  = event.headers.get ('Channel')
            actionid = event.headers.get ('ActionID')
            # test: probably not working as it strips running counter
            # at least for asterisk 1.8
            if channel :
                channel = '-'.join (channel.split ('-') [:-1])
            if channel in self.open_by_chan :
                call = self.open_by_chan [channel]
                del self.open_by_chan [channel]
                call.set_id (event)
            account = event.headers.get ('AccountCode')
            if account in self.open_by_acct :
                call = self.open_by_acct [account]
                del self.open_by_acct [account]
                call.set_id (event)
            if callid in self.open_by_id or actionid in self.open_calls :
                # Handle event with actionid first, otherwise this
                # event might never get handled as the call may already
                # be finished -- might result in reason not getting set
                # from OriginateResponse.
                self._handle_queued_event (event)
                if actionid in self.open_calls and callid :
                    call = self.open_calls [actionid]
                    call.set_id (event)
            else :
                self.unhandled.append (event)
    # end def queue_handler

    def register (self, call) :
        """ Called when one of our calls knows its callid. """
        assert (call.callid not in self.open_by_id)
        self.open_by_id [call.callid] = call
        new_unhandled = []
        for e in self.unhandled :
            if not self._handle_queued_event (e) :
                new_unhandled.append (e)
        self.unhandled = new_unhandled
    # end def register

    def unregister (self, call) :
        if not call :
            del self.closed_calls [call.actionid]
    # end def unregister

    __del__ = close

    def __getattr__ (self, name) :
        if name != 'manager' and self.manager and not name.startswith ('__') :
            result = getattr (self.manager, name)
            setattr (self, name, result)
            return result
        raise AttributeError (name)
    # end def __getattr__

    def _handle_queued_event (self, event) :
        """ Try handling the event. Returns True on success False
            otherwise.
        """
        #print ("Handling event: %s" % event.name, event.headers, file = stderr)
        uniqueid = event.headers ['Uniqueid']
        callid   = call_id (uniqueid)
        actionid = event.headers.get ('ActionID')
        if callid in self.open_by_id :
            call = self.open_by_id [callid]
            call.append (event)
            if not call :
                actionid = call.actionid
                self.closed_calls [actionid] = call
                del self.open_calls [actionid]
                del self.open_by_id [callid]
            return True
        elif actionid :
            call = self.open_calls.get (actionid)
            if call is not None :
                call.append (event)
                if not call :
                    self.closed_calls [actionid] = call
                    del self.open_calls [actionid]
                return True
        return False
    # end def _handle_queued_event

# end class Call_Manager

def parse_events (filename) :
    """ Parse events from the given event dump file.
        Mainly used for testing.
    """
    # avoid needing newer version of pyst
    from asterisk.astemu import Event
    f = open (filename, 'r')
    events = []
    lines  = []
    for line in f :
        line = line.strip ('\n')
        line = line.strip ('\r')
        if line :
            lines.append (line)
        elif lines :
            events.append (Event (l.split (': ') for l in lines))
            lines = []
    if lines :
        events.append (Event (l.split (': ') for l in lines))
    return events
# end def parse_events

if __name__ == "__main__" :
    import sys
    number = sys.argv [1]
    cm = Call_Manager ()
    cm.call (number)
    for k, v in cm.closed_calls.iteritems () :
        print ("Call: %s: %s (%s)" % (k, v.causetext, v.dialstatus))
        for event in v.events :
            print ("  Event: %s" % event.name)
            for ek, ev in event.headers.iteritems () :
                print ("    %s: %s" % (ek, ev))
    cm.close ()
