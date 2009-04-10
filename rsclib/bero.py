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

bnfos_confmap = \
    [ ( "sz"     , 'b', 1, "sz=%s"    , "szenario(0)")
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
    , ( "apwd"   , 'd', 3, "apwd=%s"  , None)
    , ( "mhost"  , 's', 2, "mhost=%s" , "netconf(5)")
    , ( "mfrom"  , 's', 2, "mfrom=%s" , "netconf(7)")
    , ( "mto"    , 's', 2, "mto=%s"   , "netconf(8)")
    , ( "XXXXX"  , 'n', 7, ""         , None)
    , ( "log"    , 'b', 3, "syslog=%s", "config(10,1)")
    , ( "loghost", 'a', 3, "slgip=%s" , "netconf(9)")
    , ( "logport", 'p', 3, "slgpt=%s" , "netconf(10)")
    , ( "wen"    , 'b', 6, "wen=%s"   , "wdog(0)")
    , ( "wen"    , 'b', 2, "wen=%s"   , "config(6,1)")
    , ( "wstate" ,   0, 6, "wstate=%s", "wdog(0)")
    , ( "wintv"  , 'p', 2, "wintv=%s" , "config(8,?)")
    , ( "as"     , 'b', 2, "as=%s"    , "config(9,1)")
    , ( "men"    , 'b', 2, "men=%s"   , "config(7,1)")
    , ( "wretv"  ,   0, 0, None       , "wdog(2)")
    ]

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

    def __init__ (self, key, type, cmd, param, macro) :
        self.key   = key
        self.type  = type
        self.cmd   = cmd
        self.param = param
        self.macro = macro
        self.value = None
        self.by_lowlevel_command [(key, cmd)] = self
    # end def __init__

    @classmethod
    def set_command (cls, key, cmd, command, helptext) :
        self = cls.by_lowlevel_command [(key, cmd)]
        self.command  = command
        self.helptext = helptext
        cls.by_highlevel_command [command] = self
    # end def set_command

    @classmethod
    def get_config (cls, host, port = 80) :
        pass
    # end def get_config
# end class Bnfos_Command

for b in bnfos_confmap :
    Bnfos_Command (*b)
for c in bnfos_commands :
    Bnfos_Command.set_command (*c)
