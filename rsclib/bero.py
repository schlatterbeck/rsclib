#!/usr/bin/python
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

from urllib2 import urlopen

# Taken from src/beronet/confmap_fos.h in the linux command-line tool
# with some additions of commands showing up in /config.txt of
# web-interface.
#       key,    type, cmd, param,       macro
bnfos_confmap = \
    [ ( "sz"     , 'b', 1, "sz=%s"    , "szenario(0)")
    , ( "szd00"  ,   0, 1, ""         , "")            ## not in bntools code
    , ( "szd01"  ,   0, 1, ""         , "")            ## not in bntools code
    , ( "mode"   , 'b', 4, "mode=%s"  , "mode(0)")
    , ( "rm"     , 'b', 1, "rm=%s"    , "config(1,1)")
    , ( "p0"     , 'b', 5, "p=0&s=%s" , "pwrport(0,0)")
    , ( "p0"     , 'b', 1, "p0=%s"    , "config(2,1)")
    , ( "p1"     , 'b', 5, "p=1&s=%s" , "pwrport(0,1)")
    , ( "p1"     , 'b', 1, "p1=%s"    , "config(3,1)")
    , ( "dn"     , 'h', 3, "dn=%s"    , "hostname(1)")
    , ( "ip"     , 'a', 3, "ip=%s"    , "netconf(0)")
    , ( "nm"     , 'a', 3, "nm=%s"    , "netconf(1)")
    , ( "gw"     , 'a', 3, "gw=%s"    , "netconf(2)")
    , ( "dns"    , 'a', 3, "dns=%s"   , "netconf(3)")
    , ( "dhcp"   , 'b', 3, "dhcp=%s"  , "config(4,1)")
    , ( "port"   , 'p', 3, "port=%s"  , "netconf(6)")
    , ( "pwd"    , 'b', 3, "pwd=%s"   , "config(5,1)")
    , ( "apwd"   , 'd', 3, "apwd=%s"  , None)          #### not in cmd list
    , ( "mail"   ,   0, 2, ""         , "")            ## not in bntools code
    , ( "mhost"  , 's', 2, "mhost=%s" , "netconf(5)")
    , ( "mfrom"  , 's', 2, "mfrom=%s" , "netconf(7)")
    , ( "mto"    , 's', 2, "mto=%s"   , "netconf(8)")
    , ( "XXXXX"  , 'n', 7, ""         , None)          #### not in cmd list
    , ( "log"    , 'b', 3, "syslog=%s", "config(10,1)")
    , ( "loghost", 'a', 3, "slgip=%s" , "netconf(9)")
    , ( "logport", 'p', 3, "slgpt=%s" , "netconf(10)") #### not in cmd list
    , ( "wen"    , 'b', 6, "wen=%s"   , "wdog(0)")
    , ( "wen"    , 'b', 2, "wen=%s"   , "config(6,1)")
    , ( "wstate" ,   0, 6, "wstate=%s", "wdog(0)")
    , ( "wintv"  , 'p', 2, "wintv=%s" , "config(8,?)")
    , ( "as"     , 'b', 2, "as=%s"    , "config(9,1)")
    , ( "men"    , 'b', 2, "men=%s"   , "config(7,1)")
    , ( "wretv"  ,   0, 0, None       , "wdog(2)")
    ]

# Taken from bnfos/main.c -- command-line interface
#      key,     cmd,  command,   helptext
bnfos_commands = \
    [ ("sz"     , 1, "scenario", "scenario (0=fallback; 1=bypass)")
    , ("mode"   , 4, "mode", "relais mode (0=A--D; 1=A--B or A--B,C--D)")
    , ("rm"     , 1, "modedef",
                           "default relais mode (0=A--D; 1=A--B or A--B,C--D)")
    , ("p0"     , 5, "power1", "state of powerport 1 (0=off; 1=on)")
    , ("p0"     , 1, "power1def", "default state of powerport 1 (0=off; 1=on)")
    , ("p1"     , 5, "power2", "state of powerport 2 (0=off; 1=on)")
    , ("p1"     , 1, "power2def", "default state of powerport 2 (0=off; 1=on)")
    , ("dn"     , 3, "hostname", "device hostname")
    , ("ip"     , 3, "address", "ip address")
    , ("nm"     , 3, "netmask", "netmask address")
    , ("gw"     , 3, "gateway", "gateway address")
    , ("dns"    , 3, "dns", "dns server address")
    , ("dhcp"   , 3, "dhcp", "query dhcp server (0=off; 1=on)")
    , ("port"   , 3, "port", "http listen port")
    , ("pwd"    , 3, "pwd", "http password protection (0=off; 1=on)")
    , ("apwd"   , 3, "apwd", "admin password")
    , ("mhost"  , 2, "smtpserv", "smtp server")
    , ("mfrom"  , 2, "smtpfrom", "smtp sender address")
    , ("mto"    , 2, "smtpto", "smtp destination address")
    , ("XXXXX"  , 7, "smtptest", "trigger testmail")
    , ("log"    , 3, "syslog", "syslog logging (0=off; 1=on)")
    , ("loghost", 3, "slgip", "syslog server ip")
    , ("logport", 3, "slgpt", "syslog server port")
    , ("wen"    , 6, "wdog", "watchdog enable (0=off; 1=on)")
    , ("wen"    , 2, "wdogdef", "default watchdog enable (0=off; 1=on)")
    , ("wstate" , 6, "wdogstate", "watchdog state (0=off; 1=on; 2=failure)")
    , ("wintv"  , 2, "wdogitime", "watchdog intervall time")
    , ("as"     , 2, "wdogaudio", "watchdog audio alarm (0=off; 1=on)")
    , ("men"    , 2, "wdogmail", "watchdog alarm mails (0=off; 1=on)")
    , ("wretv"  , 0, "wdogrtime", "watchdog remaining time to failure")
    ]

class Bnfos_Command (object) :
    by_lowlevel_command  = {}
    by_highlevel_command = {}
    by_cmd               = {}
    dirty_dict           = {}
    site = 'http://%(host)s:%(port)s/'
    host = None
    port = 80

    def __init__ (self, key, type, cmd, param, macro) :
        self.key    = key
        self.type   = type
        self.cmd    = cmd
        self.param  = param
        self.macro  = macro
        self._value = None
        self.get    = getattr (self, 'get_%s' % type)
        self.set    = self.get
        self.by_lowlevel_command [(key, cmd)] = self
        if cmd not in self.by_cmd :
            self.by_cmd [cmd] = []
        self.by_cmd [cmd].append (self)
    # end def __init__

    @classmethod
    def get_config (cls, host, port = 80) :
        cls.host = host
        cls.port = port
        url = (cls.site + "config.txt") % locals ()
        for n, line in enumerate (urlopen (url)) :
            line = line.strip ()
            if not line :
                continue
            if not line [0].isdigit () :
                assert (n == 0)
                continue
            k, v = line.split ('=')
            cmd, key = k.split ('_')
            cmd = int (cmd)
            c = cls.by_lowlevel_command [(key, cmd)]
            if not c.dirty :
                c._value = v
    # end def get_config

    @classmethod
    def set_command (cls, key, cmd, command, helptext) :
        self = cls.by_lowlevel_command [(key, cmd)]
        self.command  = command
        self.helptext = helptext
        if self.macro is None :
            self.helptext = ' '.join ((helptext, '[only set]'))
        if self.param is None :
            self.helptext = ' '.join ((helptext, '[only get]'))
        cls.by_highlevel_command [command] = self
    # end def set_command

    @classmethod
    def update_config (cls) :
        if not cls.dirty_dict :
            return
        site = cls.site % cls.__dict__
        url = []
        cmds = sorted (cmd for key, cmd in cls.dirty_dict)
        for cmd in cmds :
            url.append ('cmd=%(cmd)s' % locals ())
            for c in cls.by_cmd [cmd] :
                if c.param and (c.macro or c.dirty) :
                    url.append (c.param % c.value)
        url = '?'.join ((site, '&'.join (url)))
        urlopen (url).read ()
        #print url # resulting url for debugging
        cls.dirty_dict = {}
    # end def update_config

    @classmethod
    def usage (cls) :
        u = []
        l = 0
        for k, c in cls.by_highlevel_command.iteritems () :
            param = "<%(key)s>" % c.__dict__
            if c.type == 'b' :
                param = '{0|1}'
            if c.type == 'p' :
                param = '{1..%d}' % (2**16 - 1)
            u.append (("%(k)s=%(param)s" % locals (), c.helptext))
            l = max (len (u [-1][0]), l)
        usage = '\n'.join ("%%%ds %%s" % l % (c, h) for c, h in sorted (u))
        return usage
    # end def usage

    def get_b (self, val) :
        if val == "checked" or val == "1" or val == 1 :
            return 1
        return 0
    # end def get_b

    def get_a (self, val) :
        a     = val.split ('.')
        valid = True
        for i in a :
            try :
                i = int (i)
                if i < 0 or i > 255 :
                    valid = False
            except ValueError :
                valid = False
        if len (a) != 4 or not valid :
            raise ValueError, "Invalid Address: %s" % val
        return val
    # end def get_a

    def get_s (self, val) :
        return str (val)
    # end def get_s
    get_h = get_p = get_0 = get_n = get_d = get_s

    def getval (self) :
        return self.get (self._value)
    # end def getval

    def setval (self, value) :
        v = self.set (value)
        if v is not None :
            self._value = v
            self.dirty_dict [self.key, self.cmd] = True
    # end def setval

    def is_dirty (self) :
        return (self.key, self.cmd) in self.dirty_dict
    # end def is_dirty

    dirty = property (is_dirty)
    value = property (getval, setval)

# end class Bnfos_Command

for b in bnfos_confmap :
    Bnfos_Command (*b)
for c in bnfos_commands :
    Bnfos_Command.set_command (*c)

def main () :
    from   optparse import OptionParser
    call = 'usage: %prog [options] [parameter]* [parameter=value]*'
    parser = OptionParser (usage = '\n'.join ((call, Bnfos_Command.usage ())))
    parser.add_option \
        ( "-H", "--host"
        , dest    = "host"
        , help    = "bero*fos host, default=%default"
        , default = "fos"
        )
    parser.add_option \
        ( "-p", "--port"
        , dest    = "port"
        , help    = "port number of bero*fos http server, default=%default"
        , type    = "int"
        , default = 80
        )
    (opts, args) = parser.parse_args ()
    if not len (args) :
        parser.error ("At least one parameter is needed")
    Bnfos_Command.get_config (host = opts.host, port = opts.port)
    for a in args :
        try :
            command, value = a.split ("=", 1)
        except ValueError :
            command = a
            value   = None
        if command not in Bnfos_Command.by_highlevel_command :
            parser.error ("not a valid parameter: %s" % command)
        if value is not None :
            try :
                Bnfos_Command.by_highlevel_command [command].value = value
            except ValueError, cause :
                parser.error (cause)
        else :
            c = Bnfos_Command.by_highlevel_command [command]
            if c.macro is not None :
                print "=".join ((c.command, str (c.value)))
    Bnfos_Command.update_config ()
# end def main

if __name__ == '__main__' :
    main ()
