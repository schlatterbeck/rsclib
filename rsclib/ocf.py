#!/usr/bin/python

import os
import sys
from   rsclib.autosuper import autosuper
from   rsclib.execute   import Exec, Exec_Error
#from   config           import Config
from   rsclib.Version   import VERSION

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
        self.log.debug ("args parsed ok")
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

def main (args, cls = LSB_Resource) :
    rsrc = cls ()
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