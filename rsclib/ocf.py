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

import os
import sys
from   time               import sleep
from   rsclib.autosuper   import autosuper
from   rsclib.execute     import Exec, Exec_Error
from   rsclib.Version     import VERSION
from   rsclib.bero        import Bnfos_Command
from   rsclib.Config_File import Config_File
from   rsclib.lcr         import LCR_Port, LCR_Ports

class Parameter_Error (ValueError) : pass

class Parameter (autosuper) :
    def __init__ \
        ( self
        , name
        , description
        , type    = "string"
        , unique  = 0
        , default = None
        , **kw
        ) :
        self.name      = name
        self.longdesc  = description
        self.shortdesc = description.split ('\n', 1) [0]
        self.type      = type
        self.unique    = 0
        self.default   = default
        if default :
            self.default = 'default="%s"' % default
        else :
            self.default = ''
        self.__super.__init__ (**kw)
    # end def __init__

    def as_xml (self) :
        return """
            <parameter name="%(name)s" unique="%(unique)s">
            <longdesc lang="en">%(longdesc)s</longdesc>
            <shortdesc lang="en">%(shortdesc)s</shortdesc>
            <content type="%(type)s" %(default)s/>
            </parameter>
            """ % self.__dict__
    # end def as_xml
# end class Parameter

class Resource (Exec) :
    """ Base class for OCF Resource Agent for Heartbeat V.2 Cluster
        Resource Manager (CRM) later known as Pacemaker.
        See also the Open Cluster Framework (OCF) specification:
        http://www.opencf.org/cgi-bin/viewcvs.cgi/specs/ra/resource-agent-api.txt?rev=HEAD
    """

    xml_template = """<?xml version="1.0"?>
       <!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">
       <resource-agent name="%(name)s">
       <version>%(version)s</version>
       <longdesc lang="en">
       %(longdesc)s
       </longdesc>
       <shortdesc lang="en">%(shortdesc)s</shortdesc>
       <parameters>
       %(parameter_description)s
       </parameters>
       <actions>
       <action name="start"        timeout="30"/>
       <action name="stop"         timeout="30"/>
       <action name="status"       timeout="10" depth="0" interval="10"
               start-delay="10"/>
       <action name="monitor"      timeout="10" depth="0" interval="10"
               start-delay="10"/>
       <action name="validate-all" timeout="5"/>
       <action name="meta-data"    timeout="5" />
       %(action_description)s
       </actions>
       </resource-agent>
    """

    parameters            = []
    action_description    = ''

    OCF_SUCCESS           = 0
    OCF_ERR_GENERIC       = 1
    OCF_ERR_ARGS          = 2
    OCF_ERR_UNIMPLEMENTED = 3
    OCF_ERR_PERM          = 4
    OCF_ERR_INSTALLED     = 5
    OCF_ERR_CONFIGURED    = 6
    OCF_NOT_RUNNING       = 7

    ocf_variables = \
        [ 'OCF_RA_VERSION_MAJOR' 
        , 'OCF_RA_VERSION_MINOR'
        , 'OCF_ROOT'
        , 'OCF_RESOURCE_INSTANCE'
        , 'OCF_RESOURCE_TYPE'
        , 'OCF_CHECK_LEVEL' # only for monitor
        ]

    def __init__ (self, **kw) :
        self.__super.__init__ (**kw)
        self.value = None
    # end def __init__

    def handle (self, args) :
        r = self.parse_params ()
        self.args = args
        if len (args) != 1 :
            self.log.error ("Invalid number of arguments: %s" % len (args))
            return self.OCF_ERR_ARGS
        arg = args [0]
        if arg != 'meta-data' and r :
            raise Parameter_Error, r
        if arg == 'validate-all' :
            self.log.debug ("successful validate_all")
            return self.OCF_SUCCESS
        method = getattr (self, "handle_%s" % arg.replace ('-', '_'), None)
        if not method :
            self.log.error ("Invalid argument: %s" % arg)
            return self.OCF_ERR_UNIMPLEMENTED
        return method ()
    # end def handle

    def handle_meta_data (self) :
        """ Default for the meta-data output is the docstring of the
            derived class. The docstring needs to use the OCF XML
            format.
        """
        version               = VERSION
        longdesc              = self.__doc__
        shortdesc             = self.__doc__.split ('\n', 1) [0]
        action_description    = self.action_description
        parameter_description = '\n'.join (p.as_xml () for p in self.parameters)
        name                  = self.__class__.__name__.lower ()
        print self.xml_template % locals ()
        self.log.debug ("successful meta-data")
        return self.OCF_SUCCESS
    # end def handle_meta_data

    def handle_monitor (self) :
        raise NotImplementedError
    # end def handle_monitor

    def handle_notify (self) :
        self.log.info (self.ocf_vars)
        return self.OCF_SUCCESS
    # end def handle_notify

    handle_status       = handle_monitor
    handle_start        = handle_monitor
    handle_stop         = handle_monitor

    def parse_params (self) :
        self.value = {}
        for p in self.parameters :
            try :
                self.value [p.name] = os.environ ["OCF_RESKEY_%s" % p.name]
            except KeyError :
                self.log.error ("Missing argument: %s" % p.name)
                return self.OCF_ERR_ARGS
        self.ocf_vars = {}
        for v in self.ocf_variables :
            self.ocf_vars [v] = os.environ.get (v)
        return self.OCF_SUCCESS
    # end def parse_params

    def __getattr__ (self, name) :
        """ Return value from the parsed environment """
        for d in self.value, self.ocf_vars :
            try :
                return d [name]
            except KeyError :
                pass
        raise AttributeError, name
    # end def __getattr__

# end class Resource


class LSB_Resource (Resource) :
    """ Wrapper script for broken lsb scripts
        Call a Linux Standards Base (LSB) /etc/init.d
        script that produces wrong exit codes for Pacemaker.
        In particular: If a resource is not started an LSB script should
        return exit-code 3. We handle any exit code as "not-started" and
        return OCF_NOT_RUNNING (note that the numeric value is different
        for OCF and LSB scripts)
    """

    parameters = \
        [ Parameter
            ( "service"
            , "Wrapped service\neither script-name (in /etc/init.d) or path"
            )
        ]

    def _handle (self, cmd, error_return = None) :
        error_return = error_return or self.OCF_ERR_GENERIC
        try :
            print '\n'.join (self.exec_pipe ((self.command, cmd)))
        except Exec_Error, status :
            self.log.error ("subcommand returned: %s" % status)
            return error_return
        logger = self.log.info
        if cmd == 'status' :
            logger = self.log.debug
        logger ("successful %s for %s" % (cmd, self.service))
        return self.OCF_SUCCESS
    # end def _handle

    def handle_monitor (self) :
        return self._handle ('status', self.OCF_NOT_RUNNING)
    # end def handle_monitor
    handle_status = handle_monitor

    def handle_start (self) :
        return self._handle ('start')
    # end def handle_start

    def handle_stop (self) :
        return self._handle ('stop')
    # end def handle_stop

    def parse_params (self) :
        retval = self.__super.parse_params ()
        if retval :
            return retval
        if '/' in self.service :
            self.command = self.service
            self.service = os.path.basename (self.service)
        else :
            self.command = os.path.join ('/etc/init.d', self.service)
        if not os.access (self.command, os.X_OK) :
            self.log.error ("Service %s not installed" % self.service)
            return self.OCF_ERR_INSTALLED
        return self.OCF_SUCCESS
    # end def parse_params

# end class LSB_Resource

config  = 'alarmconfig'
cfgpath = '/etc/alarmconfig'

class Config (Config_File) :
    def __init__ (self, config = config, path = cfgpath) :
        self.__super.__init__ \
            ( path, config
            , HEARTBEAT_SWITCH = {}
            )
    # end def __init__
# end class Config

default_config = Config ()

class Bero_Resource (Resource) :
    """ Script for modeling a resource that switches a Bero*fos switch.
        This service makes sure that the Bero*fos switch is in the
        correct state (the lines are switched so that we can see them)

        We get the service name and get the configuration from the
        HEARTBEAT_SWITCH configuration option from the given config.
        HEARTBEAT_SWITCH is structured as follows:
        {'service': ( bero-adr
                    , { host1: (switch-state, interface_list)
                      , host2: (switch-state, interface_list)
                      }
                    )
        , ...
        }
        service: Our Service name (parameter) -- used as key into config
        bero-adr: Address of Bero*fos switch (IP or name)
        host1: First  asterisk host, name from 'hostname -s' command
        host2: Second asterisk host, name from 'hostname -s' command
        We find out via the hostname -s command if we're the first or
        the second host.
        switch-state: state of berofos switch for this host (either 1 or
        0 depending on the status of the berofos switch in which this
        host is connected)
        interface_list: List of Linux Call Router (LCR) interfaces
        switched by the berofos

        It's possible to define several services with different
        bero*fos switches, of course the service config must match the
        heartbeat config.

        Example:
        HEARTBEAT_SWITCH = \
            {'fos': ('fos', {'fox': (0, ['Ext1']), 'dab': (1, ['Ext1'])}) }
    """

    parameters = \
        [ Parameter
            ( "service"
            , "Service-name in HEARTBEAT_SWITCH config item"
            )
        ]

    def __init__ (self, config = default_config, **kw) :
        self.__super.__init__ (**kw)
        self.cfg = config
    # end def __init__

    def handle_monitor (self) :
        try :
            Bnfos_Command.get_config (host = self.bero, port = 80)
            val = Bnfos_Command.by_highlevel_command ['mode'].value
            if val != self.switch :
                self.log.info ("not running")
                return self.OCF_NOT_RUNNING
        except URLError, msg :
            self.log.error ("URLError: %s" % msg)
        try :
            LCR_Ports (log_prefix = self.log_prefix)
        except Exec_Error, status :
            self.log.error (status)
            return self.OCF_ERR_GENERIC
        for p in LCR_Port.by_portnumber.itervalues () :
            if p.interface in self.interfaces :
                if p.l1 != 'up' or p.l2 != 'up' :
                    self.log.error ("Interface %s not up" % p.interface)
                    return self.OCF_ERR_GENERIC
                else :
                    self.interfaces [p.interface] = True
        for k, v in self.interfaces.iteritems () :
            if not v :
                self.log.error ("Interface %s not found" % k)
                return self.OCF_ERR_GENERIC
        self.log.debug ("successful status for %s" % self.service)
        return self.OCF_SUCCESS
    # end def handle_monitor
    handle_status = handle_monitor

    def handle_start (self) :
        try :
            Bnfos_Command.get_config (host = self.bero, port = 80)
            Bnfos_Command.by_highlevel_command ['mode'].value = self.switch
            Bnfos_Command.update_config ()
        except URLError, msg :
            self.log.error ("URLError: %s" % msg)
        sleep (2)
        self.log.info ("successful start")
        return self.handle_status ()
    # end def handle_start

    def handle_stop (self) :
        try :
            Bnfos_Command.get_config (host = self.bero, port = 80)
            Bnfos_Command.by_highlevel_command ['mode'].value = not self.switch
            Bnfos_Command.update_config ()
        except URLError, msg :
            self.log.error ("URLError: %s" % msg)
        sleep (2)
        self.log.info ("successful stop")
        return self.OCF_SUCCESS
    # end def handle_start

    def parse_params (self) :
        retval = self.__super.parse_params ()
        if retval :
            return retval
        hb = self.cfg.get ('HEARTBEAT_SWITCH')
        if not hb or self.service not in hb :
            self.log.error ("Heartbeat not configured")
            return self.OCF_ERR_CONFIGURED
        hb = hb [self.service]
        self.host   = self.exec_pipe (('/bin/hostname', '-s')) [0]
        self.bero   = hb [0]
        self.switch = hb [1].get (self.host)
        if self.switch is None or len (self.switch) != 2 :
            self.log.error ("Own Hostname not found")
            return self.OCF_ERR_CONFIGURED
        self.switch, self.interfaces = self.switch
        self.interfaces = dict.fromkeys (self.interfaces)
        return self.OCF_SUCCESS
    # end def parse_params

# end class Bero_Resource

def main (args, cls = LSB_Resource, **kw) :
    rsrc = cls (**kw)
    try :
        ret = rsrc.handle (args)
        sys.exit (ret)
    except Parameter_Error, val :
        sys.exit (val.args [0])
    except StandardError :
        rsrc.log_exception ()
        sys.exit (Resource.OCF_ERR_GENERIC)
# end def main

if __name__ == '__main__' :
    main (sys.argv [1:])
