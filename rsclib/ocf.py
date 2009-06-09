#!/usr/bin/python

import sys
from   comm    import Exec
from   config  import Config

class Resource (Exec) :
    """ Base class for OCF Resource Agent for Heartbeat V.2 Cluster
        Resource Manager (CRM) later known as Pacemaker.
    """

    OCF_SUCCESS           = 0
    OCF_ERR_GENERIC       = 1
    OCF_ERR_ARGS          = 2
    OCF_ERR_UNIMPLEMENTED = 3
    OCF_ERR_PERM          = 4
    OCF_ERR_INSTALLED     = 5
    OCF_ERR_CONFIGURED    = 6
    OCF_NOT_RUNNING       = 7

    def handle (self, args) :
        if len (args) < 1 or len (args) > 1 :
            return OCF_ERR_ARGS
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
        print self.__doc__
        return OCF_SUCCESS
    # end def handle_meta_data

    def handle_monitor (self) :
        raise NotImplementedError
    # end def handle_monitor
    handle_status = handle_monitor

    def handle_start (self) :
        raise NotImplementedError
    # end def handle_start

    def handle_stop (self) :
        raise NotImplementedError
    # end def handle_stop

    def handle_validate_all (self) :
        raise NotImplementedError
    # end def handle_validate_all

# end class Resource

def main (args) :
    rsrc = Resource ()
    try :
        sys.exit (rsrc.handle (args))
    except StandardError :
        rsrc.log_exception ()
        sys.exit (1)
# end def main
