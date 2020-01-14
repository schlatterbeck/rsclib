#!/usr/bin/python
# Copyright (C) 2015-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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
import os
import sys
from   time               import sleep
from   socket             import getaddrinfo, AF_INET
from   datetime           import datetime
from   rsclib.autosuper   import autosuper
from   rsclib.execute     import Exec, Exec_Error
from   rsclib.Version     import VERSION

""" Pacemaker Cluster: Cluster Resource Manager information
"""

CRM_ATTRIBUTE = "/usr/sbin/crm_attribute"
CRM_FAILCOUNT = "/usr/sbin/crm_failcount"
CRM_NODE      = "/usr/sbin/crm_node"
CRM_RESOURCE  = "/usr/sbin/crm_resource"
HOST          = "/usr/bin/host"

class Cluster_Info (autosuper) :

    def __repr__ (self) :
        d = dict (self.__dict__)
        for n in self.attributes :
            if n not in d :
                d [n] = getattr (self, n)
        f = ', '.join ("%s=%%(%s)s" % (n, n) for n in self.attributes)
        return f % d
    # end def __repr__
    __str__ = __repr__

# end class Cluster_Info

class Cluster_Node (Cluster_Info) :
    """ Encapsulate status of a single cluster node
    """

    by_name = {}
    attributes = ('name', 'number', 'ip', 'status', 'is_ok')

    def __init__ (self, name, number, ip, status) :
        self.name   = name
        self.number = int (number)
        self.ip     = ip
        self.status = status
        self.by_name [name] = self
    # end def __init__

    @property
    def is_ok (self) :
        return self.status == 'member'
    # end def is_ok

# end class Cluster_Node

class Cluster_Resource_Fail (Cluster_Info) :

    attributes = ('resourcename', 'nodename', 'failcount', 'failtime')

    def __init__ (self, resource, nodename, failcount, lastfail) :
        self.resource  = resource
        self.node      = Cluster_Node.by_name [nodename]
        self.failcount = failcount
        self.lastfail  = lastfail
        try :
            self.failcount = int (self.failcount)
        except ValueError :
            pass
        resource.append_fail (self.node, self)
    # end def __init__

    @property
    def nodename (self) :
        return self.node.name
    # end def nodename

    @property
    def resourcename (self) :
        return self.resource.name
    # end def nodename

    @property
    def failtime (self) :
        if self.lastfail :
            return self.lastfail.strftime ("%Y-%m-%d.%H:%M:%S")
        return ''
    # end def failtime

# end class Cluster_Resource_Fail

class Cluster_Resource (Cluster_Info) :

    attributes = ('name', 'nodename')

    def __init__ (self, name, node) :
        self.name      = name
        self.node      = node
        self.fail      = {}
    # end def __init__

    @property
    def nodename (self) :
        if self.node :
            return self.node.name
        return ''
    # end def nodename

    def append_fail (self, nodename, fail) :
        self.fail [nodename] = fail
    # end def append_fail

    def __repr__ (self) :
        s = [self.__super.__repr__ ()]
        for node, f in sorted (self.fail.items ()) :
            s.append ("    " + repr (f))
        return '\n'.join (s)
    # end def __repr__
    __str__ = __repr__

    def terse (self) :
        return self.__super.__repr__ ()
    # end def terse

# end class Cluster_Resource

class Cluster_Status (Exec) :

    def __init__ (self, **kw) :
        self.__super.__init__ (** kw)
        self.nodes     = {}
        self.resources = {}
        stdout = self.exec_pipe ((CRM_NODE, "-l"))
        for line in stdout :
            number, name, status = line.strip ().split ()
            ip = getaddrinfo (name, None, AF_INET) [0][-1][0]
            self.nodes [name] = Cluster_Node (name, number, ip, status)
        stdout = self.exec_pipe ((CRM_RESOURCE, "-l"))
        for line in stdout :
            rname = line.strip ()
            state = self.exec_pipe ((CRM_RESOURCE, "-W", "-r", rname))
            assert len (state) == 1
            state = state [0].strip ()
            if not state :
                state = self.stderr.strip ()
            s     = 'resource %s is ' % rname
            assert state.startswith (s)
            if state.endswith ('NOT running') :
                node      = None
            else :
                node      = state.rsplit (None, 1) [-1]
                node      = Cluster_Node.by_name [node]
            resource = Cluster_Resource (rname, node)
            self.resources [rname] = resource
            for nn in Cluster_Node.by_name :
                fail  = self.exec_pipe ((CRM_FAILCOUNT, "-r", rname, "-N", nn))
                assert len (fail) == 1
                fail  = fail [0].strip ()
                fail  = dict ((x.split ('=', 1) for x in fail.split ()))
                assert fail ['name'] == 'fail-count-%s' % rname
                assert fail ['scope'] == 'status'
                failcount = fail ['value']
                lfn  = 'last-failure-%s' % rname
                lastfail = ''
                if failcount != '0' :
                    sout = self.exec_pipe \
                        ( ( CRM_ATTRIBUTE
                          , "-t", "status", "-n", lfn, "-G", "-N", nn
                          )
                        , ignore_err = True
                        )
                    assert len (sout) == 1
                    res = dict ((x.split ('=', 1) for x in sout [0].split ()))
                else :
                    res = None
                if res :
                    if 'value' in res and res ['value'] != '(null)' :
                        assert res ['scope'] == 'status'
                        assert res ['name'] == lfn
                        lastfail = datetime.fromtimestamp (int (res ['value']))
                Cluster_Resource_Fail (resource, nn, failcount, lastfail)
    # end def __init__

    def _exec_resource_cmd (self, resourcename, nodename, cmd) :
        if resourcename not in self.resources :
            return (('Unknown resource', -1))
        if nodename :
            if nodename not in self.nodes :
                return (('Unknown node', -2))
            cmd.append ("-N")
            cmd.append (nodename)
        try :
            res = self.exec_pipe (cmd)
            self.log.debug ("Successful resource cmd: %s" % ' '.join (cmd))
            if len (res) > 1 or len (res) == 1 and res [0] :
                for r in res :
                    self.log.debug (r)
        except Exec_Error as cause :
            return cause
        return None
    # end def _exec_resource_cmd

    def clear_error (self, resourcename, nodename = None) :
        """ Clear error for a resource with optionally specified node.
        """
        cmd = [CRM_RESOURCE, "-r", resourcename, "-C"]
        return self._exec_resource_cmd (resourcename, nodename, cmd)
    # end def clear_error

    def migrate (self, resourcename, nodename = None) :
        """ Migrate a cluster resource to another node.
            Note that the destination node is optional, if the node is
            not specified, the resource manager will set constraints
            that force the recource away from the current node.
            After the move we have to clean up the temporary constraints
            that were placed for migration.
        """
        cmd = [CRM_RESOURCE, "-r", resourcename, "-M"]
        ret = self._exec_resource_cmd (resourcename, nodename, cmd)
        if ret :
            return ret
        sleep (5)
        cmd = [CRM_RESOURCE, "-r", resourcename, "-U"]
        return self._exec_resource_cmd (resourcename, None, cmd)
    # end def migrate

    def __repr__ (self) :
        res = ['Nodes:']
        for n in self.nodes.values () :
            res.append (str (n))
        res.append ('Resources:')
        for r in self.resources.values () :
            res.append (str (r))
        return '\n'.join (res)
    # end def __repr__
    __str__ = __repr__

# end class Cluster_Status


def main (args, **kw) :
    cs = Cluster_Status ()
    print (cs)
# end def main

if __name__ == '__main__' :
    main (sys.argv [1:])
