#!/usr/bin/python

import sys
from   comm           import Exec
from   config         import Config
from   rsclib.Version import VERSION

class Resource (Exec) :
    """ Base class for OCF Resource Agent for Heartbeat V.2 Cluster
        Resource Manager (CRM) later known as Pacemaker.
    """

    xml_template = """<?xml version="1.0"?>
       <!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">
       <resource-agent name="lsbwrapper">
       <version>%(VERSION)s</version>
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

    parameter_description = ''
    action_description    = ''

    OCF_SUCCESS           = 0
    OCF_ERR_GENERIC       = 1
    OCF_ERR_ARGS          = 2
    OCF_ERR_UNIMPLEMENTED = 3
    OCF_ERR_PERM          = 4
    OCF_ERR_INSTALLED     = 5
    OCF_ERR_CONFIGURED    = 6
    OCF_NOT_RUNNING       = 7

    def check_args (self) :
        if len (self.args) != 1 :
            return OCF_ERR_ARGS
        return OCF_SUCCESS
    # end def check_args

    def handle (self, args) :
        self.args = args
        ret = self.check_args ()
        if ret :
            return ret
        method = getattr (self, "handle_%s" % args [0].replace ('-', '_'), None)
        if not method :
            return OCF_ERR_ARGS
        return method (self)
    # end def handle

    def handle_meta_data (self) :
        """ Default for the meta-data output is the docstring of the
            derived class. The docstring needs to use the OCF XML
            format.
        """
        VERSION               = VERSION
        longdesc              = self.__doc__
        shortdesc             = self.__doc__.split ('\n', 1) [0]
        action_description    = self.action_description
        parameter_description = self.parameter_description
        print self.__doc__ % locals ()
        return OCF_SUCCESS
    # end def handle_meta_data

    def handle_monitor (self) :
        raise NotImplementedError
    # end def handle_monitor

    handle_status       = handle_monitor
    handle_start        = handle_monitor
    handle_stop         = handle_monitor

    def handle_validate_all (self) :
        return OCF_SUCCESS
    # end def handle_validate_all

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

    def check_args (self) :
        if len (self.args) != 2 :
            return OCF_ERR_ARGS
        self.name = self.args.pop (0)
        if '/' in self.name :
            self.command = self.name
            self.name    = os.path.basename (self.name)
        else :
            self.command = os.path.join ('/etc/init.d', self.name)
    # end def check_args

    def handle_monitor (self) :
    # end def handle_monitor
    handle_status = handle_monitor

    def handle_start (self) :
    # end def handle_start

    def handle_stop (self) :
    # end def handle_stop

# end class Resource

def main (args) :
    rsrc = Resource ()
    try :
        sys.exit (rsrc.handle (args))
    except StandardError :
        rsrc.log_exception ()
        sys.exit (1)
# end def main

if __name__ == '__main__' :
    main (sys.argv [1:])
